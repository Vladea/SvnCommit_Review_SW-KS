from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import DATABASE_URL


engine = create_engine(
    DATABASE_URL,
    connect_args={'check_same_thread': False} if DATABASE_URL.startswith('sqlite') else {}
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def session():
    return SessionLocal()


def init_db():
    from app.models import commit, changed_file, review_issue, daily_report, author_stat
    Base.metadata.create_all(bind=engine)
