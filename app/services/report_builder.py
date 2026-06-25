from collections import defaultdict

from sqlalchemy import or_

from app.models import DailyReport, AuthorStat, SvnCommit, ReviewIssue
from app.database import session


def create_report(s, start_date, end_date, touched_keys=None, matched_logs=None, skipped_logs=None):
    touched_keys = touched_keys or []
    if touched_keys:
        clauses = [
            (SvnCommit.project_name == p) & (SvnCommit.revision == r)
            for p, r in touched_keys
        ]
        commits = s.query(SvnCommit).filter(or_(*clauses)).all() if clauses else []
    else:
        commits = []

    keys = {(c.project_name, c.revision) for c in commits}
    issues = []
    if keys:
        issue_clauses = [
            (ReviewIssue.project_name == p) & (ReviewIssue.revision == r)
            for p, r in keys
        ]
        issues = s.query(ReviewIssue).filter(or_(*issue_clauses)).all()

    pm = defaultdict(lambda: {'commits': 0, 'files': 0, 'authors': set(), 'issues': []})
    am = defaultdict(lambda: {'commits': 0, 'files': 0, 'projects': set(),
                               'P1': 0, 'P2': 0, 'P3': 0, 'P4': 0})

    for c in commits:
        pm[c.project_name]['commits'] += 1
        pm[c.project_name]['files'] += c.changed_file_count or 0
        pm[c.project_name]['authors'].add(c.author)
        am[c.author]['commits'] += 1
        am[c.author]['files'] += c.changed_file_count or 0
        am[c.author]['projects'].add(c.project_name)

    for i in issues:
        pm[i.project_name]['issues'].append(i)
        if i.author in am and i.level in ['P1', 'P2', 'P3', 'P4']:
            am[i.author][i.level] += 1

    counts = {lv: sum(1 for i in issues if i.level == lv) for lv in ['P1', 'P2', 'P3', 'P4']}
    file_total = sum(c.changed_file_count or 0 for c in commits)

    lines = [
        f'\U0001f4ca 代码审查报告（{end_date}）',
        '',
        f'\U0001f4c1 审查仓库：{len(pm)} 个',
        f'\U0001f4dd 变更提交：{len(commits)} 个',
        f'\U0001f4c4 变更文件：{file_total} 个',
        f'\U0001f465 涉及提交人：{len(am)} 人',
        f'\u23f1\ufe0f SVN提交日期范围：{start_date} ~ {end_date}',
        '\n\u2501' * 15,
        '\u2705 一、项目审查结果',
        '\u2501' * 15
    ]

    for idx, (p, v) in enumerate(pm.items(), 1):
        ps = {lv: sum(1 for i in v['issues'] if i.level == lv) for lv in ['P1', 'P2', 'P3', 'P4']}
        if ps['P1'] == ps['P2'] == ps['P3'] == 0:
            result = '未发现关键问题'
        else:
            result = f'P1:{ps["P1"]} P2:{ps["P2"]} P3:{ps["P3"]} P4:{ps["P4"]}'
        lines += [
            f'\n{idx}. {p}',
            f'- 提交数量：{v["commits"]} 个',
            f'- 变更文件：{v["files"]} 个',
            f'- 涉及提交人：{len(v["authors"])} 人',
            f'- 审查结果：{result}'
        ]

    lines.append('\n\u2501' * 15 + '\n\U0001f4cc 二、实际命中的 Revision\n' + '\u2501' * 15)
    if matched_logs:
        for x in matched_logs[:80]:
            lines.append(
                f'- 项目：{x.get("project")} Revision：{x.get("revision")} '
                f'提交人：{x.get("author")} 提交日期：{x.get("commit_date_local")} '
                f'提交时间：{x.get("commit_time_local")}'
            )
    else:
        lines.append('- 本日期范围内没有真实 SVN commit。')

    lines.append('\n\u2501' * 15 + '\n\U0001f465 三、提交人统计\n' + '\u2501' * 15)
    sorted_authors = sorted(
        am.items(),
        key=lambda x: (x[1]['P1'], x[1]['P2'], x[1]['P3'], x[1]['commits']),
        reverse=True
    )
    for idx, (a, v) in enumerate(sorted_authors, 1):
        lines += [
            f'\n{idx}. {a or "unknown"}',
            f'- 提交次数：{v["commits"]}',
            f'- 变更文件：{v["files"]}',
            f'- P1：{v["P1"]}，P2：{v["P2"]}，P3：{v["P3"]}，P4：{v["P4"]}'
        ]

    lines += [
        '\n\u2501' * 15 + '\n\U0001f6a8 四、高风险问题\n' + '\u2501' * 15,
        '今日未发现 P1 Critical 问题。' if counts['P1'] == 0 else '发现 P1 Critical 问题，请立即确认。',
        f'P1：{counts["P1"]}，P2：{counts["P2"]}，P3：{counts["P3"]}，P4：{counts["P4"]}'
    ]

    if skipped_logs:
        lines += [
            '\n\u2501' * 15,
            '\u2139\ufe0f SVN 日期粗筛返回但被真实提交日期过滤掉的 Revision',
            '\u2501' * 15
        ]
        for x in skipped_logs[:50]:
            lines.append(
                f'- 项目：{x.get("project")} Revision：{x.get("revision")} '
                f'提交日期：{x.get("commit_date_local")} 提交时间：{x.get("commit_time_local")}'
            )

    report = DailyReport(
        report_date=end_date, start_date=start_date, end_date=end_date,
        repo_count=len(pm), commit_count=len(commits), file_count=file_total,
        author_count=len(am),
        p1_count=counts['P1'], p2_count=counts['P2'], p3_count=counts['P3'], p4_count=counts['P4'],
        report_markdown='\n'.join(lines)
    )
    s.add(report)
    s.flush()

    for a, v in am.items():
        total = v['P1'] + v['P2'] + v['P3'] + v['P4']
        s.add(AuthorStat(
            report_id=report.id, author=a, commit_count=v['commits'],
            changed_file_count=v['files'], project_count=len(v['projects']),
            p1_count=v['P1'], p2_count=v['P2'], p3_count=v['P3'], p4_count=v['P4'],
            issue_density=total / v['commits'] if v['commits'] else 0
        ))
    s.commit()
    return report
