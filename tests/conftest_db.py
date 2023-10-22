import contextlib
from typing import Any, Generator

import pytest
from sqlalchemy import create_engine  # type: ignore
from sqlalchemy.engine.base import Engine  # type: ignore
from sqlalchemy.orm import Session, sessionmaker  # type: ignore

from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware
from antarest.dbmodel import Base

__all__ = ("db_engine_fixture", "db_session_fixture", "db_middleware_fixture")


@pytest.fixture(name="db_engine")
def db_engine_fixture() -> Generator[Engine, None, None]:
    """
    Fixture that creates an in-memory SQLite database engine for testing.

    Yields:
        An instance of the created SQLite database engine.
    """
    engine = create_engine("sqlite:///:memory:")
    engine.execute("PRAGMA foreign_keys = ON")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(name="db_session")
def db_session_fixture(db_engine: Engine) -> Generator[Session, None, None]:
    """
    Fixture that creates a database session for testing purposes.

    This fixture uses the provided db engine fixture to create a session maker,
    which in turn generates a new database session bound to the specified engine.

    Args:
        db_engine: The database engine instance provided by the db_engine fixture.

    Yields:
        A new SQLAlchemy session object for database operations.
    """
    make_session = sessionmaker(bind=db_engine)
    with contextlib.closing(make_session()) as session:
        yield session


@pytest.fixture(name="db_middleware", autouse=True)
def db_middleware_fixture(
    db_engine: Engine,
) -> Generator[DBSessionMiddleware, None, None]:
    """
    Fixture that sets up a database session middleware with custom engine settings.

    Args:
        db_engine: The database engine instance created by the db_engine fixture.

    Yields:
        An instance of the configured DBSessionMiddleware.
    """
    yield DBSessionMiddleware(
        None,
        custom_engine=db_engine,
        session_args={"autocommit": False, "autoflush": False},
    )
