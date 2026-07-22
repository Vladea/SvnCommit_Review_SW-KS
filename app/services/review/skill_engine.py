import logging

from app.config import skills_cfg, get_active_llm_provider
from app.services.review.llm import _get_client

logger = logging.getLogger('svn_ai_review')


def review(project, rev, author, file_path, diff_text, commit_message):
    provider = get_active_llm_provider()
    if not provider:
        logger.warning(f'Skill review skipped: no active LLM provider')
        return []

    client = _get_client(provider)
    skills = [s for s in skills_cfg() if s.get('enabled')]
    if not skills:
        logger.info(f'Skill review skipped: no enabled skills')
        return []

    lower = str(file_path).lower()
    matched = [s for s in skills if any(lower.endswith('.' + ext.lstrip('.')) for ext in s.get('file_types', []))]
    if not matched:
        return []

    issues = []
    for skill in matched:
        prompt = (
            f'{skill["prompt"]}\n\n'
            f'文件：{file_path}\n'
            f'Commit 信息：{commit_message}\n'
            f'Diff：\n{diff_text}'
        )
        try:
            result = client.review_with_prompt(prompt)
            skill_issues = result.get('issues', [])
            logger.info(f'Skill [{skill["id"]}] found {len(skill_issues)} issues for {file_path}')
            for issue in skill_issues:
                issues.append({
                    'project_name': project,
                    'revision': rev,
                    'author': author,
                    'level': issue.get('level', skill.get('level', 'P4')),
                    'issue_type': f'skill:{skill["id"]}',
                    'file_path': file_path,
                    'line_no': str(issue.get('line', 'unknown')),
                    'description': issue.get('desc', ''),
                    'reason': '',
                    'suggestion': issue.get('suggestion', ''),
                    'need_manual_check': 1,
                    'engine_type': 'skill',
                })
        except Exception as e:
            logger.error(f'Skill [{skill["id"]}] review failed for {file_path}: {e}')

    return issues
