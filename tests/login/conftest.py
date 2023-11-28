import pytest

from antarest.core.config import Config
from antarest.core.interfaces.eventbus import IEventBus
from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware
from antarest.login.ldap import LdapService
from antarest.login.repository import BotRepository, GroupRepository, RoleRepository, UserLdapRepository, UserRepository
from antarest.login.service import LoginService


# noinspection PyUnusedLocal
@pytest.fixture(name="group_repo")
def group_repo_fixture(db_middleware: DBSessionMiddleware) -> GroupRepository:
    """Fixture that creates a GroupRepository instance."""
    # note: `DBSessionMiddleware` is required to instantiate a thread-local db session.
    # important: the `GroupRepository` insert an admin group in the database if it does not exist:
    # >>> Group(id="admin", name="admin")
    return GroupRepository()


# noinspection PyUnusedLocal
@pytest.fixture(name="user_repo")
def user_repo_fixture(db_middleware: DBSessionMiddleware) -> UserRepository:
    """Fixture that creates a UserRepository instance."""
    # note: `DBSessionMiddleware` is required to instantiate a thread-local db session.
    # important: the `UserRepository` insert an admin user in the database if it does not exist.
    # >>> User(id=1, name="admin", password=Password(config.security.admin_pwd))
    return UserRepository()


# noinspection PyUnusedLocal
@pytest.fixture(name="user_ldap_repo")
def user_ldap_repo_fixture(db_middleware: DBSessionMiddleware) -> UserLdapRepository:
    """Fixture that creates a UserLdapRepository instance."""
    # note: `DBSessionMiddleware` is required to instantiate a thread-local db session.
    return UserLdapRepository()


# noinspection PyUnusedLocal
@pytest.fixture(name="bot_repo")
def bot_repo_fixture(db_middleware: DBSessionMiddleware) -> BotRepository:
    """Fixture that creates a BotRepository instance."""
    # note: `DBSessionMiddleware` is required to instantiate a thread-local db session.
    return BotRepository()


# noinspection PyUnusedLocal
@pytest.fixture(name="role_repo")
def role_repo_fixture(db_middleware: DBSessionMiddleware) -> RoleRepository:
    """Fixture that creates a RoleRepository instance."""
    # note: `DBSessionMiddleware` is required to instantiate a thread-local db session.
    # important: the `RoleRepository` insert an admin role in the database if it does not exist.
    # >>> Role(type=RoleType.ADMIN, identity=User(id=1), group=Group(id="admin"))
    return RoleRepository()


@pytest.fixture(name="ldap_service")
def ldap_service_fixture(
    core_config: Config,
    user_ldap_repo: UserLdapRepository,
    group_repo: GroupRepository,
    role_repo: RoleRepository,
) -> LdapService:
    """Fixture that creates a LdapService instance."""
    return LdapService(
        config=core_config,
        users=user_ldap_repo,
        groups=group_repo,
        roles=role_repo,
    )


@pytest.fixture(name="login_service")
def login_service_fixture(
    user_repo: UserRepository,
    bot_repo: BotRepository,
    group_repo: GroupRepository,
    role_repo: RoleRepository,
    ldap_service: LdapService,
    event_bus: IEventBus,
) -> LoginService:
    """Fixture that creates a LoginService instance."""
    return LoginService(
        user_repo=user_repo,
        bot_repo=bot_repo,
        group_repo=group_repo,
        role_repo=role_repo,
        ldap=ldap_service,
        event_bus=event_bus,
    )
