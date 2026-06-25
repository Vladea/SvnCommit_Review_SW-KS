import json
import logging
import os
import re
import time

import requests

logger = logging.getLogger('svn_ai_review')


class OpenAICompatibleClient:
    def __init__(self, provider_cfg):
        self.name = provider_cfg.get('name', provider_cfg.get('id', ''))
        self.api_base = provider_cfg['api_base'].rstrip('/')
        self.api_key = os.getenv(provider_cfg.get('api_key_ref', ''), '')
        self.model = provider_cfg['model']
        self.timeout = 120

    def _chat(self, prompt):
        r = requests.post(
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
        return r.json()['choices'][0]['message']['content']

    def review(self, project, rev, author, file_path, diff_text, commit_message):
        prompt = (
            '请对以下 SVN diff 做 Review，只输出 JSON。'
            f'文件：{file_path}\n'
            f'Commit: {commit_message}\n'
            f'Diff:\n{diff_text}'
        )
        try:
            content = self._chat(prompt)
            data = json.loads(re.search(r'\{.*\}', content, re.S).group(0))
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
                return {'ok': True, 'elapsed_ms': elapsed, 'detail': r.json()['choices'][0]['message']['content'][:50]}
            return {'ok': False, 'elapsed_ms': elapsed, 'detail': f'HTTP {r.status_code}: {r.text[:200]}'}
        except Exception as e:
            elapsed = round((time.time() - start) * 1000)
            return {'ok': False, 'elapsed_ms': elapsed, 'detail': str(e)}


def llm_review(project, rev, author, file_path, diff_text, commit_message):
    from app.config import get_active_llm_provider

    provider = get_active_llm_provider()
    if not provider:
        return []

    client = OpenAICompatibleClient(provider)
    return client.review(project, rev, author, file_path, diff_text, commit_message)
