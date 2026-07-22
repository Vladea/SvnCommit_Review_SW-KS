import json
import logging
import os
import re
import time

import requests

logger = logging.getLogger('svn_ai_review')

_clients = {}


class OpenAICompatibleClient:
    def __init__(self, provider_cfg):
        self.name = provider_cfg.get('name', provider_cfg.get('id', ''))
        self.api_base = provider_cfg['api_base'].strip().rstrip('/')
        self.api_key = os.getenv(provider_cfg.get('api_key_ref', ''), '')
        self.model = provider_cfg['model']
        self.timeout = 120
        self._session = None

    @property
    def session(self):
        if self._session is None:
            self._session = requests.Session()
        return self._session

    def _chat(self, prompt):
        from app.config import llm_cfg
        cfg = llm_cfg()
        retry_count = cfg.get('retry_count', 2)
        retry_delay = cfg.get('retry_delay', 5)

        last_err = None
        for attempt in range(retry_count + 1):
            try:
                r = self.session.post(
                    self.api_base + '/chat/completions',
                    headers={
                        'Authorization': f'Bearer {self.api_key}',
                        'Content-Type': 'application/json'
                    },
                    json={
                        'model': self.model,
                        'messages': [{'role': 'user', 'content': prompt}],
                        'temperature': 0.1
                    },
                    timeout=self.timeout
                )
                r.raise_for_status()
                data = r.json()
                try:
                    return data['choices'][0]['message']['content']
                except (KeyError, IndexError, TypeError):
                    raise RuntimeError(f'Unexpected API response: {str(data)[:200]}')
            except Exception as e:
                last_err = e
                if attempt < retry_count:
                    wait = retry_delay * (2 ** attempt)
                    logger.warning(f'[{self.name}] LLM attempt {attempt + 1}/{retry_count + 1} failed: {e}. Retrying in {wait}s...')
                    time.sleep(wait)
        raise last_err

    @staticmethod
    def _extract_json(text):
        if not text:
            return {}

        m = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                pass

        start = text.find('{')
        if start == -1:
            return {}
        depth = 0
        for i in range(start, len(text)):
            ch = text[i]
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except json.JSONDecodeError:
                        return {}
        try:
            return json.loads(text[start:])
        except json.JSONDecodeError:
            return {}

    def review(self, project, rev, author, file_path, diff_text, commit_message):
        prompt = (
            '请对以下 SVN diff 做 Review，只输出 JSON。'
            f'文件：{file_path}\n'
            f'Commit: {commit_message}\n'
            f'Diff:\n{diff_text}'
        )
        try:
            content = self._chat(prompt)
            data = self._extract_json(content)
        except Exception as e:
            logger.error(f'[{self.name}] Review failed for {file_path}: {e}')
            return []

        issues = []
        for i in data.get('issues', []):
            issues.append({
                'project_name': project,
                'revision': rev,
                'author': author,
                'level': i.get('level', 'P4'),
                'issue_type': i.get('type', 'general'),
                'file_path': i.get('file', file_path),
                'line_no': str(i.get('line', 'unknown')),
                'description': i.get('description', ''),
                'reason': i.get('reason', ''),
                'suggestion': i.get('suggestion', ''),
                'need_manual_check': 1 if i.get('need_manual_check', True) else 0,
                'engine_type': 'llm'
            })
        return issues

    def review_with_prompt(self, prompt):
        content = self._chat(prompt)
        return self._extract_json(content)

    def test_connection(self):
        start = time.time()
        try:
            r = requests.post(
                self.api_base + '/chat/completions',
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': self.model,
                    'messages': [{'role': 'user', 'content': '回复 OK'}],
                    'max_tokens': 10
                },
                timeout=30
            )
            elapsed = round((time.time() - start) * 1000)
            if r.status_code == 200:
                data = r.json()
                try:
                    detail = data['choices'][0]['message']['content'][:50]
                except (KeyError, IndexError, TypeError):
                    detail = str(data)[:200]
                return {'ok': True, 'elapsed_ms': elapsed, 'detail': detail}
            return {'ok': False, 'elapsed_ms': elapsed, 'detail': f'HTTP {r.status_code}: {r.text[:200]}'}
        except Exception as e:
            elapsed = round((time.time() - start) * 1000)
            return {'ok': False, 'elapsed_ms': elapsed, 'detail': str(e)}


def _get_client(provider_cfg):
    pid = provider_cfg.get('id', '')
    if pid not in _clients:
        _clients[pid] = OpenAICompatibleClient(provider_cfg)
    return _clients[pid]


def llm_review(project, rev, author, file_path, diff_text, commit_message):
    from app.config import get_active_llm_provider

    provider = get_active_llm_provider()
    if not provider:
        return []

    client = _get_client(provider)
    return client.review(project, rev, author, file_path, diff_text, commit_message)
