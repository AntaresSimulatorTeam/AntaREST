import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session  # type: ignore

from antarest.common.config import Config, SecurityConfig
from antarest.login.repository import (
    UserRepository,
    GroupRepository,
    RoleRepository,
    BotRepository,
)
from antarest.common.persistence import Base
from antarest.login.model import User, RoleType, Password, Group, Role, Bot


@pytest.mark.unit_test
def test_users():
    engine = create_engine("sqlite:///:memory:", echo=True)
    session = scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=engine)
    )
    Base.metadata.create_all(engine)

    repo = UserRepository(
        config=Config(security=SecurityConfig(admin_pwd="admin")),
        session=session,
    )
    a = User(
        name="a",
        password=Password("a"),
    )
    b = User(name="b", password=Password("b"))

    a = repo.save(a)
    b = repo.save(b)
    assert b.id
    c = repo.get(a.id)
    assert a == c
    assert a.password.check("a")
    assert b == repo.get_by_name("b")

    repo.delete(a.id)
    assert repo.get(a.id) is None


@pytest.mark.unit_test
def test_bots():
    engine = create_engine("sqlite:///:memory:", echo=True)
    session = scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=engine)
    )

    Base.metadata.create_all(engine)

    repo = BotRepository(session=session)

    a = Bot(name="a", owner=1)

    a = repo.save(a)
    assert a.id
    assert a == repo.get(a.id)
    assert [a] == repo.get_all_by_owner(1)

    with pytest.raises(ValueError):
        repo.save(a)

    assert repo.exists(a.id)

    repo.delete(a.id)
    assert repo.get(a.id) is None


@pytest.mark.unit_test
def test_groups():
    engine = create_engine("sqlite:///:memory:", echo=True)
    session = scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=engine)
    )

    Base.metadata.create_all(engine)

    repo = GroupRepository(session=session)

    a = Group(name="a")

    a = repo.save(a)
    assert a.id
    assert a == repo.get(a.id)

    repo.delete(a.id)
    assert repo.get(a.id) is None


@pytest.mark.unit_test
def test_roles():
    engine = create_engine("sqlite:///:memory:", echo=True)
    session = scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=engine)
    )

    Base.metadata.create_all(engine)

    repo = RoleRepository(session=session)

    a = Role(type=RoleType.ADMIN, identity=User(id=0), group=Group(id="group"))

    a = repo.save(a)
    assert a == repo.get(user=0, group="group")
    assert [a] == repo.get_all_by_user(user=0)
    assert [a] == repo.get_all_by_group(group="group")

    repo.delete(user=0, group="group")
    assert repo.get(user=0, group="group") is None
