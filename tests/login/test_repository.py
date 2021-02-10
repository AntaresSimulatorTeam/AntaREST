from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session  # type: ignore

from antarest.common.config import Config
from antarest.common.persistence import Base
from antarest.login.model import User, Role, Password, Group
from antarest.login.repository import UserRepository, GroupRepository


def test_users():
    engine = create_engine("sqlite:///:memory:", echo=True)
    session = scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=engine)
    )
    Base.metadata.create_all(engine)

    repo = UserRepository(
        config=Config({"login": {"admin": {"pwd": "admin"}}}), session=session
    )
    a = User(
        name="a",
        role=Role.ADMIN,
        password=Password("a"),
        groups=[Group(name="a")],
    )
    b = User(name="b", role=Role.ADMIN, password=Password("b"))

    a = repo.save(a)
    b = repo.save(b)
    assert b.id
    c = repo.get(a.id)
    assert a == c
    assert a.password.check("a")
    assert b == repo.get_by_name("b")

    repo.delete(a.id)
    assert repo.get(a.id) is None


def test_groups():
    engine = create_engine("sqlite:///:memory:", echo=True)
    session = scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=engine)
    )

    Base.metadata.create_all(engine)

    repo = GroupRepository(config=Config(), session=session)

    a = Group(
        name="a",
        users=[User(name="a", role=Role.ADMIN, password=Password("a"))],
    )

    a = repo.save(a)
    assert a.id
    assert a == repo.get(a.id)

    repo.delete(a.id)
    assert repo.get(a.id) is None
