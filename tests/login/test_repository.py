import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker  # type: ignore

from antarest.core.config import Config, SecurityConfig
from antarest.core.persistence import Base
from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware, db
from antarest.login.model import Bot, Group, Password, Role, RoleType, User, UserLdap
from antarest.login.repository import BotRepository, GroupRepository, RoleRepository, UserLdapRepository, UserRepository


@pytest.mark.unit_test
def test_users():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    # noinspection SpellCheckingInspection
    DBSessionMiddleware(
        None,
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )

    with db():
        repo = UserRepository(
            config=Config(security=SecurityConfig(admin_pwd="admin")),
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
def test_users_ldap():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    # noinspection SpellCheckingInspection
    DBSessionMiddleware(
        None,
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )

    with db():
        repo = UserLdapRepository()
        a = UserLdap(name="a", external_id="b")

        a = repo.save(a)
        assert a.id

        assert repo.get_by_external_id("b") == a

        repo.delete(a.id)
        assert repo.get(a.id) is None


@pytest.mark.unit_test
def test_bots():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    # noinspection SpellCheckingInspection
    DBSessionMiddleware(
        None,
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )

    with db():
        repo = BotRepository()
        a = Bot(name="a", owner=1)
        a = repo.save(a)
        assert a.id
        assert a == repo.get(a.id)
        assert [a] == repo.get_all_by_owner(1)
        assert a == repo.get_by_name_and_owner(owner=1, name="a")
        assert not repo.get_by_name_and_owner(owner=1, name="wrong_name")
        assert not repo.get_by_name_and_owner(owner=9, name="a")

        with pytest.raises(ValueError):
            repo.save(a)

        assert repo.exists(a.id)

        repo.delete(a.id)
        assert repo.get(a.id) is None


@pytest.mark.unit_test
def test_groups():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    # noinspection SpellCheckingInspection
    DBSessionMiddleware(
        None,
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )

    with db():
        repo = GroupRepository()

        a = Group(name="a")

        a = repo.save(a)
        assert a.id
        assert a == repo.get(a.id)

        b = repo.get_by_name(a.name)
        assert b == a

        repo.delete(a.id)
        assert repo.get(a.id) is None


@pytest.mark.unit_test
def test_roles():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    # noinspection SpellCheckingInspection
    DBSessionMiddleware(
        None,
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )

    with db():
        repo = RoleRepository()

        a = Role(
            type=RoleType.ADMIN, identity=User(id=0), group=Group(id="group")
        )

        a = repo.save(a)
        assert a == repo.get(user=0, group="group")
        assert [a] == repo.get_all_by_user(user=0)
        assert [a] == repo.get_all_by_group(group="group")

        repo.delete(user=0, group="group")
        assert repo.get(user=0, group="group") is None
