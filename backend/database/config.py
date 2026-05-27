from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "openMinistry"
    debug: bool = False
    secret_key: str
    database_url: str
    redis_url: str

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


class Base(DeclarativeBase):
    pass


def get_engine():
    settings = get_settings()
    return create_engine(
        settings.database_url,
        echo=settings.debug,  # logs SQL queries in debug mode
        pool_pre_ping=True,   # checks connection is alive before using it
    )


def get_session_factory():
    engine = get_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency — yields a database session per request."""
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()