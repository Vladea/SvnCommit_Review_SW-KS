from sqlalchemy import Column, Integer, String, Float

from app.database import Base


class AuthorStat(Base):
    __tablename__ = 'author_stats'

    id = Column(Integer, primary_key=True)
    report_id = Column(Integer, nullable=False)
    author = Column(String, default='')
    commit_count = Column(Integer, default=0)
    changed_file_count = Column(Integer, default=0)
    project_count = Column(Integer, default=0)
    p1_count = Column(Integer, default=0)
    p2_count = Column(Integer, default=0)
    p3_count = Column(Integer, default=0)
    p4_count = Column(Integer, default=0)
    issue_density = Column(Float, default=0.0)
