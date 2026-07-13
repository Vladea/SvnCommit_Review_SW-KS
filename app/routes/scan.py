import threading

from fastapi import APIRouter, Query

from app.schemas.scan import ScanRangeRequest
from app.services.scanner import run_range, run_daily_job
from app.services import scan_progress

router = APIRouter(tags=['scan'])


@router.post('/scan/range')
def scan_range(req: ScanRangeRequest):
    return run_range(req.start_date, req.end_date, req.project_names, req.push_teams)


@router.post('/jobs/run-daily')
def daily():
    return run_daily_job()


@router.get('/scan/start')
def scan_start(
    start_date: str = Query(...),
    end_date: str = Query(...),
    project_names: list[str] | None = Query(None),
    push_teams: bool = Query(True),
    max_commits: int | None = Query(None),
    preview: bool = Query(False),
):
    from app.config import enabled_projects
    from app.services.svn_client import svn_logs, filter_logs_by_real_commit_date

    projects = enabled_projects()
    if project_names:
        projects = [p for p in projects if p.get('name') in project_names]

    matched_all = []
    skipped_all = []
    for p in projects:
        name = p.get('name', 'unknown')
        try:
            raw_logs = svn_logs(p['svn_url'], start_date, end_date)
            logs, skipped = filter_logs_by_real_commit_date(raw_logs, start_date, end_date)
            for x in skipped:
                x['project'] = name
                skipped_all.append(x)
            for log in logs:
                matched_all.append({
                    'project': name,
                    'revision': log.get('revision', ''),
                    'author': log.get('author', ''),
                    'commit_date_local': log.get('commit_date_local', ''),
                    'commit_time_local': log.get('commit_time_local', ''),
                })
        except Exception as e:
            matched_all.append({
                'project': name, 'revision': 'unknown', 'author': 'unknown',
                'commit_date_local': '', 'commit_time_local': '',
                'error': str(e)
            })

    total = len(matched_all)
    if preview and total > 5:
        max_commits = 5

    sid = scan_progress.create(total, matched_all, skipped_all, is_preview=preview)

    def _run():
        try:
            def cb(data):
                scan_progress.update(
                    sid,
                    status='running',
                    current_project=data.get('project', ''),
                    current_revision=data.get('revision', ''),
                    current_file=data.get('file', ''),
                    completed=data.get('completed', 0),
                )
            result = run_range(start_date, end_date, project_names, push_teams,
                               progress_callback=cb, max_commits=max_commits)
            scan_progress.finish(sid, result)
        except Exception as e:
            scan_progress.fail(sid, e)

    threading.Thread(target=_run, daemon=True).start()
    return {
        'scan_id': sid,
        'total_commits': total,
        'matched_logs': matched_all[:100],
        'skipped_logs': skipped_all[:50],
        'is_preview': preview,
        'preview_triggered': preview and total > 5,
    }


@router.get('/scan/progress/{scan_id}')
def scan_progress_route(scan_id: str):
    return scan_progress.get(scan_id)
