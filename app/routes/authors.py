from fastapi import APIRouter

from app.database import session
from app.models.daily_report import DailyReport
from app.models.author_stat import AuthorStat

router = APIRouter(prefix='/authors', tags=['authors'])


@router.get('/latest')
def authors_latest():
    s = session()
    try:
        r = s.query(DailyReport).order_by(DailyReport.id.desc()).first()
        if not r:
            return []
        rows = s.query(AuthorStat).filter_by(report_id=r.id).all()
        return [{
            'author': x.author, 'commit_count': x.commit_count,
            'file_count': x.changed_file_count, 'project_count': x.project_count,
            'p1': x.p1_count, 'p2': x.p2_count, 'p3': x.p3_count, 'p4': x.p4_count,
            'density': x.issue_density
        } for x in rows]
    finally:
        s.close()
