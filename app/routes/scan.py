import threading

from fastapi import APIRouter, Query

from app.schemas.scan import ScanRangeRequest
from app.services.scanner import run_range, run_daily_job, collect_commits
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
    matched_all, skipped_all, _errors = collect_commits(start_date, end_date, project_names)

    total = len(matched_all)
    if preview and total > 5:
        max_commits = 5 if max_commits is None else min(max_commits, 5)

    matched_logs = [{'project': m['project'], 'revision': m['revision'],
                     'author': m['author'], 'commit_date_local': m['commit_date_local'],
                     'commit_time_local': m['commit_time_local']} for m in matched_all]

    sid = scan_progress.create(total, matched_logs, skipped_all, is_preview=preview)

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
                               progress_callback=cb, max_commits=max_commits, scan_id=sid)
            scan_progress.finish(sid, result)
        except Exception as e:
            scan_progress.fail(sid, e)

    t = threading.Thread(target=_run, daemon=False)
    t.start()
    return {
        'scan_id': sid,
        'total_commits': total,
        'matched_logs': matched_logs[:100],
        'skipped_logs': skipped_all[:50],
        'is_preview': preview,
        'preview_triggered': preview and total > 5,
    }


@router.get('/scan/progress/{scan_id}')
def scan_progress_route(scan_id: str):
    return scan_progress.get(scan_id)


@router.post('/scan/cancel/{scan_id}')
def scan_cancel(scan_id: str):
    scan_progress.cancel(scan_id)
    return {'scan_id': scan_id, 'cancelled': True}
