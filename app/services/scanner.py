import json
import logging

from app.database import session
from app.config import enabled_projects, scan_cfg, LOCAL_TZ, notification_cfg
from app.models import SvnCommit, ReviewIssue
from app.services.svn_client import svn_logs, filter_logs_by_real_commit_date, svn_diff_safe, split_diff, should_review
from app.services.review.rule_engine import rule_review
from app.services.review.llm import llm_review
from app.services.report_builder import create_report
from app.services.notifier import send_notification
from app.models.changed_file import ChangedFile

logger = logging.getLogger('svn_ai_review')


def run_range(start_date, end_date, project_names=None, push=True):
    s = session()
    new = []
    errors = []
    touched_keys = []
    matched_logs = []
    skipped_logs = []
    try:
        projects = enabled_projects()
        if project_names:
            projects = [p for p in projects if p.get('name') in project_names]

        for p in projects:
            name = p.get('name', 'unknown')
            try:
                raw_logs = svn_logs(p['svn_url'], start_date, end_date)
                logs, skipped = filter_logs_by_real_commit_date(raw_logs, start_date, end_date)
                for x in skipped:
                    x['project'] = name
                    skipped_logs.append(x)
                logger.info(f'Project [{name}]: {len(logs)} commits matched, {len(skipped)} skipped')
            except Exception as e:
                errors.append({
                    'project': name, 'revision': 'unknown', 'author': 'unknown', 'error': str(e)
                })
                logger.error(f'Project [{name}] svn log error: {e}')
                continue

            for log in logs:
                rev = log.get('revision', '')
                touched_keys.append((name, rev))
                matched_logs.append({
                    'project': name, 'revision': rev, 'author': log.get('author', ''),
                    'commit_date_local': log.get('commit_date_local', ''),
                    'commit_time_local': log.get('commit_time_local', '')
                })

                if s.query(SvnCommit).filter_by(project_name=name, revision=rev).first():
                    continue

                try:
                    raw = svn_diff_safe(p['svn_url'], rev)
                except Exception as e:
                    errors.append({
                        'project': name, 'revision': rev, 'author': log.get('author', 'unknown'), 'error': str(e)
                    })
                    logger.error(f'Project [{name}] rev [{rev}] diff error: {e}')
                    continue

                diff_map = split_diff(raw)
                max_chars = int(scan_cfg().get('max_diff_chars_per_file', 12000))
                c = SvnCommit(
                    project_name=name, branch='', revision=rev,
                    author=log.get('author', ''),
                    commit_time=log.get('commit_time_local') or log.get('commit_time', ''),
                    message=log.get('message', ''),
                    changed_file_count=len(diff_map)
                )
                s.add(c)
                s.flush()
                new.append(c)

                for fp, diff in diff_map.items():
                    short = diff[:max_chars]
                    try:
                        need = 1 if should_review(fp) else 0
                    except Exception as e:
                        errors.append({
                            'project': name, 'revision': rev, 'author': c.author,
                            'error': f'should_review failed: {e}'
                        })
                        need = 0

                    s.add(ChangedFile(
                        commit_id=c.id, file_path=fp, diff_text=short,
                        diff_size=len(short), need_review=need
                    ))

                    if need:
                        try:
                            for issue in rule_review(name, rev, c.author, fp, short) + \
                                    llm_review(name, rev, c.author, fp, short, c.message):
                                s.add(ReviewIssue(**issue))
                        except Exception as e:
                            errors.append({
                                'project': name, 'revision': rev, 'author': c.author,
                                'error': f'review failed: {e}'
                            })
                            logger.error(f'Review failed for {name} r{rev} {fp}: {e}')
                s.commit()

        report = create_report(s, start_date, end_date, touched_keys, matched_logs, skipped_logs)
        if errors:
            lines = ['', '\u2501' * 30, '\u26a0\ufe0f SVN / Review \u91c7\u96c6\u5f02\u5e38', '\u2501' * 30]
            for err in errors:
                lines.append(
                    f'- \u9879\u76ee\uff1a{err.get("project", "unknown")} '
                    f'Revision\uff1a{err.get("revision", "unknown")} '
                    f'\u63d0\u4ea4\u4eba\uff1a{err.get("author", "unknown")} '
                    f'\u9519\u8bef\uff1a{err.get("error", "")}'
                )
            report.report_markdown += '\n' + '\n'.join(lines)
            s.commit()

        if push:
            results = send_notification(report.report_markdown)
            report.teams_push_status = json.dumps(results, ensure_ascii=False)
            s.commit()
            logger.info(f'Report [{report.id}] push result: {results}')

        logger.info(
            f'Scan complete: {len(new)} new commits, {len(matched_logs)} revisions, '
            f'{len(skipped_logs)} skipped, {len(errors)} errors'
        )
        return {
            'new_commit_count': len(new),
            'matched_revision_count': len(matched_logs),
            'skipped_by_date_count': len(skipped_logs),
            'report_id': report.id,
            'errors': errors,
            'matched_logs': matched_logs,
            'skipped_logs': skipped_logs[:50],
            'report': report.report_markdown
        }
    finally:
        s.close()


def last_day_range_by_date():
    today = datetime.now(LOCAL_TZ).date()
    yesterday = today - timedelta(days=1)
    return yesterday.isoformat(), today.isoformat()


def run_daily_job():
    start_date, end_date = last_day_range_by_date()
    return run_range(start_date, end_date, None, True)
