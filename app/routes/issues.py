from fastapi import APIRouter

from app.database import session
from app.models.review_issue import ReviewIssue

router = APIRouter(prefix='/issues', tags=['issues'])


@router.get('')
def list_issues():
    s = session()
    try:
        rows = s.query(ReviewIssue).order_by(ReviewIssue.id.desc()).limit(300).all()
        return [{
            'id': x.id, 'project': x.project_name, 'revision': x.revision,
            'author': x.author, 'level': x.level, 'type': x.issue_type,
            'file': x.file_path, 'desc': x.description,
            'suggestion': x.suggestion, 'status': x.status
        } for x in rows]
    finally:
        s.close()
