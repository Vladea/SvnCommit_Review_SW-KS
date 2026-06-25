from fastapi import APIRouter

from app.schemas.scan import ScanRangeRequest
from app.services.scanner import run_range, run_daily_job

router = APIRouter(tags=['scan'])


@router.post('/scan/range')
def scan_range(req: ScanRangeRequest):
    return run_range(req.start_date, req.end_date, req.project_names, req.push_teams)


@router.post('/jobs/run-daily')
def daily():
    return run_daily_job()
