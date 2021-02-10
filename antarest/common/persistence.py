from contextlib import contextmanager
from typing import Any, Generator

from sqlalchemy.engine import Engine  # type: ignore
from sqlalchemy.ext.declarative import declarative_base  # type: ignore
from sqlalchemy.orm import Session, sessionmaker  # type: ignore

Base = declarative_base()


class DTO:
    """
    Implement basic method for DTO objects
    """

    def __hash__(self) -> int:
        return hash(tuple(sorted(self.__dict__.items())))

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, type(self)) and self.__dict__ == other.__dict__
        )

    def __str__(self) -> str:
        return "{}({})".format(
            type(self).__name__,
            ", ".join(
                [
                    "{}={}".format(k, str(self.__dict__[k]))
                    for k in sorted(self.__dict__)
                ]
            ),
        )

    def __repr__(self) -> str:
        return self.__str__()


@contextmanager
def session_scope(engine: Engine) -> Generator[Session, Any, Any]:
    """Provide a transactional scope around a series of operations."""
    try:
        Session = sessionmaker(engine, expire_on_commit=False)
        sess = Session()
        yield sess
        sess.commit()
    except:
        sess.rollback()
        raise
    finally:
        sess.close()
