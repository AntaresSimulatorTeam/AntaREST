from contextvars import ContextVar, Token
from typing import Any, Dict, Optional, Type, Union

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

_Session: Optional[sessionmaker[Session]] = None
_session: ContextVar[Optional[Session]] = ContextVar("_session", default=None)


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


class DBSessionMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: Optional[ASGIApp],
        db_url: Optional[Union[str, URL]] = None,
        custom_engine: Optional[Engine] = None,
        engine_args: Optional[Dict[str, Any]] = None,
        session_args: Optional[Dict[str, Any]] = None,
        commit_on_exit: bool = False,
    ) -> None:
        if app:
            super().__init__(app)
        global _Session
        engine_args = engine_args or {}
        self.commit_on_exit = commit_on_exit

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


class DBSession(metaclass=DBSessionMeta):
    def __init__(
        self,
        session_args: Optional[Dict[str, Any]] = None,
        commit_on_exit: bool = False,
    ) -> None:
        self.token: Optional[Token[Optional[Any]]] = None
        self.session_args = session_args or {}
        self.commit_on_exit = commit_on_exit

    def __enter__(self) -> Type["DBSession"]:
        if not isinstance(_Session, sessionmaker):
            raise SessionNotInitialisedError
        self.token = _session.set(_Session(**self.session_args))
        return type(self)

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        sess: Optional[Session] = _session.get()
        if sess is not None:
            if exc_type is not None:
                sess.rollback()

            if self.commit_on_exit:
                sess.commit()

            sess.close()
        if self.token is not None:
            _session.reset(self.token)


db: Type[DBSession] = DBSession
