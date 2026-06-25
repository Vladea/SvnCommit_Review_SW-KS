from sqlalchemy import Column, Integer, String, Text

from app.database import Base


class ChangedFile(Base):
    __tablename__ = 'changed_files'

    id = Column(Integer, primary_key=True)
    commit_id = Column(Integer, nullable=False)
    file_path = Column(Text, default='')
    change_type = Column(String, default='M')
    diff_text = Column(Text, default='')
    diff_size = Column(Integer, default=0)
    need_review = Column(Integer, default=1)
