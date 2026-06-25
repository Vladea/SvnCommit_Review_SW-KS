from fastapi import APIRouter

from app.database import session
from app.models import SvnCommit, ReviewIssue, DailyReport

router = APIRouter(tags=['dashboard'])


@router.get('/dashboard/summary')
def dashboard():
    s = session()
    try:
        latest = s.query(DailyReport).order_by(DailyReport.id.desc()).first()
        return {
            'commit_count': s.query(SvnCommit).count(),
            'issue_count': s.query(ReviewIssue).count(),
            'report_count': s.query(DailyReport).count(),
            'latest_report': latest.report_markdown if latest else ''
        }
    finally:
        s.close()
