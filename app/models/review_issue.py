from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from datetime import datetime

from app.database import Base


class ReviewIssue(Base):
    __tablename__ = 'review_issues'

    id = Column(Integer, primary_key=True)
    project_name = Column(String, default='')
    revision = Column(String, default='')
    author = Column(String, default='')
    level = Column(String, default='P4', index=True)
    issue_type = Column(String, default='general')
    file_path = Column(Text, default='')
    line_no = Column(String, default='unknown')
    description = Column(Text, default='')
    reason = Column(Text, default='')
    suggestion = Column(Text, default='')
    need_manual_check = Column(Integer, default=1)
    engine_type = Column(String, default='rule')
    status = Column(String, default='Open')
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('ix_review_issues_project_rev', 'project_name', 'revision'),
        Index('ix_review_issues_engine', 'engine_type'),
    )
