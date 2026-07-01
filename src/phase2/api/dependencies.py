from collections.abc import Generator

from fastapi import Request
from sqlalchemy.orm import Session

from src.phase1.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "")
