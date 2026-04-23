from collections.abc import Callable
from contextvars import ContextVar, Token
from typing import Any, TypeAlias

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import URL
from sqlalchemy.event import listen
from sqlalchemy.orm import Session, sessionmaker
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp
from typing_extensions import override

from antarest.core.utils.fastapi_sqlalchemy.exceptions import MissingSessionError, SessionNotInitialisedError

_Session: sessionmaker[Session] | None = None
_session: ContextVar[Session | None] = ContextVar("_session", default=None)


def _is_sqlite_engine(engine: Engine) -> bool:
    return "sqlite" in engine.url.drivername.lower()


def enable_sqlite_foreign_keys(dbapi_connection: Any, connection_record: Any) -> None:
    """
    By default, sqlite does not enforce foreign key constraints,
    we need to tell it explicitly.
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()


def init_db_singleton(
    db_url: str | URL | None = None,
    custom_engine: Engine | None = None,
    engine_args: dict[str, Any] | None = None,
    session_args: dict[str, Any] | None = None,
) -> None:
    global _Session
    engine_args = engine_args or {}

    session_args = session_args or {}
    if not custom_engine and not db_url:
        raise ValueError("You need to pass a db_url or a custom_engine parameter.")
    if not custom_engine:
        assert db_url is not None, "Database URL cannot be None"
        engine = create_engine(db_url, **engine_args)
    else:
        engine = custom_engine

    if _is_sqlite_engine(engine):
        listen(engine, "connect", enable_sqlite_foreign_keys)

    _Session = sessionmaker(bind=engine, **session_args)


class DBSessionMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp | None,
        commit_on_exit: bool = False,
    ) -> None:
        if app:
            super().__init__(app)
        self.commit_on_exit = commit_on_exit

    @override
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        with db(commit_on_exit=self.commit_on_exit):
            response = await call_next(request)
        return response


class DBSessionMeta(type):
    # using this metaclass means that we can access db.session as a property at a class level,
    # rather than db().session
    @property
    def session(self) -> Session:
        """Return an instance of Session local to the current async context."""
        if _Session is None:
            raise SessionNotInitialisedError

        session = _session.get()
        if session is None:
            raise MissingSessionError

        return session


SessionFactory: TypeAlias = Callable[[], Session]


def _default_create_session() -> Session:
    if isinstance(_Session, sessionmaker):
        return _Session()
    raise SessionNotInitialisedError()


class DBSession(metaclass=DBSessionMeta):
    def __init__(
        self,
        session_factory: SessionFactory = _default_create_session,
        commit_on_exit: bool = False,
    ) -> None:
        self.token: Token[Any | None] | None = None
        self.session_factory = session_factory
        self.commit_on_exit = commit_on_exit

    def __enter__(self) -> type["DBSession"]:
        self.token = _session.set(self.session_factory())
        return type(self)

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        sess = _session.get()
        if sess is not None:
            try:
                # it's important to either commit or rollback in all cases.
                # this correctly closes the ongoing transaction. Otherwise,
                # closing the session may raise an error (for example on server disconnect)
                # without correctly closing the transaction. It can result in particular
                # in wrong metrics.
                if self.commit_on_exit and exc_value is None:
                    sess.commit()
                else:
                    sess.rollback()
            finally:
                sess.close()

        if self.token is not None:
            _session.reset(self.token)


db: type[DBSession] = DBSession
