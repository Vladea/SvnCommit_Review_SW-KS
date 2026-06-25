from fastapi import APIRouter

from app.database import session
from app.models.daily_report import DailyReport

router = APIRouter(prefix='/reports', tags=['reports'])


@router.get('')
def list_reports():
    s = session()
    try:
        rows = s.query(DailyReport).order_by(DailyReport.id.desc()).limit(50).all()
        return [{
            'id': r.id, 'date': r.report_date, 'repo_count': r.repo_count,
            'commit_count': r.commit_count, 'file_count': r.file_count,
            'author_count': r.author_count,
            'p1': r.p1_count, 'p2': r.p2_count, 'p3': r.p3_count, 'p4': r.p4_count,
            'teams': r.teams_push_status
        } for r in rows]
    finally:
        s.close()


@router.get('/{rid}')
def report_detail(rid: int):
    s = session()
    try:
        r = s.query(DailyReport).get(rid)
        return {'id': r.id, 'report': r.report_markdown} if r else {}
    finally:
        s.close()
