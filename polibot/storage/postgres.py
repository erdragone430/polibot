from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from polibot.config import get_settings
from polibot.storage.models import Base

settings = get_settings()
engine = create_engine(settings.postgres_dsn)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def ensure_tables() -> None:
    Base.metadata.create_all(bind=engine)
