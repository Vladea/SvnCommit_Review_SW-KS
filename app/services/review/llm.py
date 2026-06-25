import json
import logging
import re

import requests

from app.config import LLM_PROVIDER, LLM_API_BASE, LLM_API_KEY, LLM_MODEL

logger = logging.getLogger('svn_ai_review')


def llm_review(project, rev, author, file_path, diff_text, commit_message):
    if LLM_PROVIDER == 'mock':
        return []

    prompt = (
        '请对以下 SVN diff 做 Review，只输出 JSON。'
        f'文件：{file_path}\n'
        f'Commit: {commit_message}\n'
        f'Diff:\n{diff_text}'
    )

    try:
        r = requests.post(
            LLM_API_BASE.rstrip('/') + '/chat/completions',
            headers={'Authorization': 'Bearer ' + LLM_API_KEY, 'Content-Type': 'application/json'},
            json={
                'model': LLM_MODEL,
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': 0.1
            },
            timeout=120
        )
        r.raise_for_status()
        content = r.json()['choices'][0]['message']['content']
        data = json.loads(re.search(r'\{.*\}', content, re.S).group(0))
    except Exception as e:
        logger.error(f'LLM review failed for {file_path}: {e}')
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
