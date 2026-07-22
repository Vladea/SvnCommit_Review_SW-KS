from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, UniqueConstraint, Index

from app.database import Base


class SvnCommit(Base):
    __tablename__ = 'svn_commits'

    id = Column(Integer, primary_key=True)
    project_name = Column(String, nullable=False)
    revision = Column(String, nullable=False)
    author = Column(String, default='')
    commit_time = Column(DateTime, nullable=True)
    message = Column(Text, default='')
    changed_file_count = Column(Integer, default=0)
    scanned_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('project_name', 'revision', name='uix_project_revision'),
        Index('ix_svn_commits_author', 'author'),
        Index('ix_svn_commits_commit_time', 'commit_time'),
    )
