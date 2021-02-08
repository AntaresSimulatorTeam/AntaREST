from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from antarest.common.config import Config
from antarest.common.dto import Base
from antarest.login.model import User, Role, Password, Group
from antarest.login.repository import UserRepository, GroupRepository


def test_users():
    engine = create_engine("sqlite:///:memory:", echo=True)

    Base.metadata.create_all(engine)

    repo = UserRepository(
        config=Config({"login": {"admin": {"pwd": "admin"}}}), engine=engine
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

    Base.metadata.create_all(engine)

    repo = GroupRepository(config=Config(), engine=engine)

    a = Group(
        name="a",
        users=[User(name="a", role=Role.ADMIN, password=Password("a"))],
    )

    a = repo.save(a)
    assert a.id
    assert a == repo.get(a.id)
