from sqlalchemy.engine.base import Engine  # type: ignore
from sqlalchemy.orm import sessionmaker  # type: ignore

from antarest.login.model import GROUP_ID, GROUP_NAME, USER_ID, USER_NAME, Group, Password, Role, User, init_admin_user
from antarest.utils import SESSION_ARGS

TEST_ADMIN_PASS_WORD = "test"


def test_password():
    assert Password("pwd").check("pwd")


class TestInitAdminUser:
    def test_nominal_init_admin_user(self, db_engine: Engine):
        init_admin_user(db_engine, dict(SESSION_ARGS), admin_password=TEST_ADMIN_PASS_WORD)
        make_session = sessionmaker(bind=db_engine)
        with make_session() as session:
            user = session.query(User).get(USER_ID)
            assert user is not None
            assert user.id == USER_ID
            assert user.name == USER_NAME
            assert user.password.check(TEST_ADMIN_PASS_WORD)
            group = session.query(Group).get(GROUP_ID)
            assert group is not None
            assert group.id == GROUP_ID
            assert group.name == GROUP_NAME
            role = session.query(Role).get((USER_ID, GROUP_ID))
            assert role is not None
            assert role.identity is not None
            assert role.identity.id == USER_ID
            assert role.identity.name == USER_NAME
            assert role.identity.password.check(TEST_ADMIN_PASS_WORD)
            assert role.group is not None
            assert role.group.id == GROUP_ID
            assert role.group.name == GROUP_NAME
