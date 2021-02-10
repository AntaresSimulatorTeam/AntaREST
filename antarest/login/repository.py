import uuid
from contextlib import contextmanager
from typing import Dict, Optional, List, Generator, Any

from sqlalchemy.engine import Engine  # type: ignore
from sqlalchemy.orm import Session, sessionmaker  # type: ignore

from antarest.common.config import Config
from antarest.login.model import User, Role, Password, Group


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


class GroupRepository:
    def __init__(self, config: Config, engine: Engine):
        self.engine = engine

    def save(self, group: Group) -> Group:
        with session_scope(self.engine) as sess:
            sess.add(group)
            sess.commit()
            return group

    def get(self, id: int) -> Optional[Group]:
        with session_scope(self.engine) as sess:
            group: Group = sess.query(Group).get(id)
            return group

    def get_all(self) -> List[Group]:
        with session_scope(self.engine) as sess:
            groups: List[Group] = sess.query(Group).all()
            return groups

    def delete(self, id: int) -> None:
        with session_scope(self.engine) as sess:
            g = sess.query(Group).get(id)
            sess.delete(g)


class UserRepository:
    def __init__(self, config: Config, engine: Engine) -> None:
        self.engine = engine
        self.save(
            User(
                name="admin",
                role=Role.ADMIN,
                password=Password(config["login.admin.pwd"]),
            )
        )

    def save(self, user: User) -> User:
        with session_scope(self.engine) as sess:
            sess.add(user)
            sess.commit()
            return user

    def get(self, id: int) -> Optional[User]:
        with session_scope(self.engine) as sess:
            user: User = sess.query(User).get(id)
            return user

    def get_by_name(self, name: str) -> User:
        with session_scope(self.engine) as sess:
            user: User = sess.query(User).filter_by(name=name).first()
            return user

    def get_all(self) -> List[User]:
        with session_scope(self.engine) as sess:
            users: List[User] = sess.query(User).all()
            return users

    def delete(self, id: int) -> None:
        with session_scope(self.engine) as sess:
            u: User = sess.query(User).get(id)
            sess.delete(u)
