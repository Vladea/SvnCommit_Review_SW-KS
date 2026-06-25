from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime

from app.database import Base


class DailyReport(Base):
    __tablename__ = 'daily_reports'

    id = Column(Integer, primary_key=True)
    report_date = Column(String, default='')
    start_date = Column(String, default='')
    end_date = Column(String, default='')
    repo_count = Column(Integer, default=0)
    commit_count = Column(Integer, default=0)
    file_count = Column(Integer, default=0)
    author_count = Column(Integer, default=0)
    p1_count = Column(Integer, default=0)
    p2_count = Column(Integer, default=0)
    p3_count = Column(Integer, default=0)
    p4_count = Column(Integer, default=0)
    report_markdown = Column(Text, default='')
    teams_push_status = Column(String, default='NotPushed')
    created_at = Column(DateTime, default=datetime.utcnow)
