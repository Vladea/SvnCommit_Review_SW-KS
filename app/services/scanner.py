import json
import logging
from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError

from app.database import session
from app.config import enabled_projects, scan_cfg, LOCAL_TZ
from app.models import SvnCommit, ReviewIssue
from app.models.changed_file import ChangedFile
from app.services.svn_client import svn_logs, filter_logs_by_real_commit_date, svn_diff_safe, svn_diff_summarize, split_diff, should_review, parse_svn_time_to_local
from app.services.review.rule_engine import rule_review
from app.services.review.llm import llm_review
from app.services.report_builder import create_report
from app.services.notifier import send_notification

logger = logging.getLogger('svn_ai_review')


def collect_commits(start_date, end_date, project_names=None):
    matched = []
    skipped = []
    errors = []
    projects = enabled_projects()
    if project_names:
        projects = [p for p in projects if p.get('name') in project_names]

    for p in projects:
        name = p.get('name', 'unknown')
        try:
            raw_logs = svn_logs(p['svn_url'], start_date, end_date)
            logs, skp = filter_logs_by_real_commit_date(raw_logs, start_date, end_date)
            for x in skp:
                x['project'] = name
                skipped.append(x)
            for log in logs:
                matched.append({
                    'project': name,
                    'revision': log.get('revision', ''),
                    'author': log.get('author', ''),
                    'commit_time': log.get('commit_time', ''),
                    'commit_date_local': log.get('commit_date_local', ''),
                    'commit_time_local': log.get('commit_time_local', ''),
                    'message': log.get('message', ''),
                    'svn_url': p['svn_url'],
                })
            logger.info(f'Project [{name}]: {len(logs)} commits matched, {len(skp)} skipped')
        except Exception as e:
            errors.append({'project': name, 'revision': 'unknown', 'author': 'unknown', 'error': str(e)})
            logger.error(f'Project [{name}] svn log error: {e}')
    return matched, skipped, errors


def _review_file(project, rev, author, file_path, diff_text, commit_message):
    issues = []
    try:
        for issue in rule_review(project, rev, author, file_path, diff_text) + \
                     llm_review(project, rev, author, file_path, diff_text, commit_message):
            issues.append(ReviewIssue(**issue))
    except Exception as e:
        logger.error(f'Review failed for {project} r{rev} {file_path}: {e}')
    return issues


def _process_commit(s, svn_url, log, progress_callback=None, completed=0, total=0):
    name = log['project']
    rev = log['revision']
    max_files = int(scan_cfg().get('max_files_per_commit', 10))
    max_chars = int(scan_cfg().get('max_diff_chars_per_file', 12000))

    if s.query(SvnCommit).filter_by(project_name=name, revision=rev).first():
        return None, True

    try:
        file_list = svn_diff_summarize(svn_url, rev)
    except Exception as e:
        logger.error(f'Project [{name}] rev [{rev}] summarize error: {e}')
        return {'project': name, 'revision': rev, 'author': log.get('author', 'unknown'), 'error': str(e)}, False

    if len(file_list) > max_files:
        logger.info(f'Project [{name}] rev [{rev}] skipped: {len(file_list)} files (>{max_files})')
        return None, True

    try:
        raw = svn_diff_safe(svn_url, rev)
    except Exception as e:
        logger.error(f'Project [{name}] rev [{rev}] diff error: {e}')
        return {'project': name, 'revision': rev, 'author': log.get('author', 'unknown'), 'error': str(e)}, False

    diff_map = split_diff(raw)

    c = SvnCommit(
        project_name=name, revision=rev,
        author=log.get('author', ''),
        commit_time=parse_svn_time_to_local(log.get('commit_time')) or datetime.utcnow(),
        message=log.get('message', ''),
        changed_file_count=len(diff_map)
    )
    try:
        s.add(c)
        s.flush()
    except IntegrityError:
        s.rollback()
        logger.info(f'Project [{name}] rev [{rev}] already scanned, skipped')
        return None, True

    for fp, diff in diff_map.items():
        short = diff[:max_chars]
        need = 1 if should_review(fp) else 0

        s.add(ChangedFile(
            commit_id=c.id, file_path=fp, diff_text=short,
            diff_size=len(short), need_review=need
        ))

        if progress_callback:
            progress_callback({'phase': 'scanning', 'project': name, 'revision': rev,
                               'file': fp, 'completed': completed, 'total': total})

        if need:
            for issue in _review_file(name, rev, log.get('author', ''), fp, short, log.get('message', '')):
                s.add(issue)
    s.commit()
    return c, True


def run_range(start_date, end_date, project_names=None, push=True, progress_callback=None, max_commits=None):
    s = session()
    matched, skipped, errors = collect_commits(start_date, end_date, project_names)
    new = []
    scanned = 0

    try:
        total = len(matched)
        for i, log in enumerate(matched):
            if max_commits and scanned >= max_commits:
                break

            rev = log['revision']
            name = log['project']

            if progress_callback:
                progress_callback({'phase': 'diffing', 'project': name, 'revision': rev,
                                   'file': '', 'completed': scanned, 'total': total})

            result, ok = _process_commit(s, log['svn_url'], log, progress_callback, scanned, total)
            if result is not None and not ok:
                errors.append(result)
            elif result is not None:
                new.append(result)
            scanned += 1

        touched_keys = [(m['project'], m['revision']) for m in matched]
        matched_logs = [{'project': m['project'], 'revision': m['revision'], 'author': m['author'],
                         'commit_date_local': m['commit_date_local'], 'commit_time_local': m['commit_time_local']}
                        for m in matched]
        report = create_report(s, start_date, end_date, touched_keys, matched_logs, skipped)

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

        logger.info(f'Scan complete: {len(new)} new commits, {len(matched)} revisions, {len(skipped)} skipped, {len(errors)} errors')
        return {
            'new_commit_count': len(new),
            'matched_revision_count': len(matched),
            'skipped_by_date_count': len(skipped),
            'report_id': report.id,
            'errors': errors,
            'matched_logs': matched_logs,
            'skipped_logs': skipped[:50],
            'report': report.report_markdown,
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
