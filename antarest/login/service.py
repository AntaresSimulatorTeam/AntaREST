from typing import Optional, List

import werkzeug as werkzeug

from antarest.common.custom_types import JSON
from antarest.common.interfaces.eventbus import IEventBus
from antarest.common.jwt import JWTUser, JWTGroup
from antarest.common.requests import (
    RequestParameters,
    UserHasNotPermissionError,
)
from antarest.login.ldap import LdapService
from antarest.login.model import (
    User,
    Group,
    Role,
    BotCreateDTO,
    Bot,
    Identity,
    UserCreateDTO,
    Password,
)
from antarest.login.repository import (
    UserRepository,
    GroupRepository,
    RoleRepository,
    BotRepository,
)


class GroupNotFoundError(werkzeug.exceptions.NotFound):
    pass


class UserNotFoundError(werkzeug.exceptions.NotFound):
    pass


class LoginService:
    def __init__(
        self,
        user_repo: UserRepository,
        bot_repo: BotRepository,
        group_repo: GroupRepository,
        role_repo: RoleRepository,
        ldap: LdapService,
        event_bus: IEventBus,
    ):
        self.users = user_repo
        self.bots = bot_repo
        self.groups = group_repo
        self.roles = role_repo
        self.ldap = ldap
        self.event_bus = event_bus

    # SADMIN, GADMIN (own group)
    def save_group(self, group: Group, params: RequestParameters) -> Group:
        if params.user and any(
            (params.user.is_site_admin(), params.user.is_group_admin(group))
        ):
            return self.groups.save(group)
        else:
            raise UserHasNotPermissionError()

    # SADMIN
    def create_user(
        self, create: UserCreateDTO, param: RequestParameters
    ) -> Identity:
        if param.user and param.user.is_site_admin():
            return self.users.save(
                User(name=create.name, password=Password(create.password))
            )
        else:
            raise UserHasNotPermissionError()

    # SADMIN, USER (own user)
    def save_user(self, user: User, params: RequestParameters) -> User:
        if params.user and any(
            (params.user.is_site_admin(), params.user.is_himself(user))
        ):
            return self.users.save(user)
        else:
            raise UserHasNotPermissionError()

    # User (own user)
    def save_bot(self, bot: BotCreateDTO, params: RequestParameters) -> Bot:
        if params.user:
            role = self.roles.get(params.user.id, bot.group)
            if role and role.type.is_higher_or_equals(bot.role):
                b = self.bots.save(
                    Bot(
                        name=bot.name,
                        is_author=bot.is_author,
                        owner=params.user.id,
                    )
                )
                self.roles.save(
                    Role(group=Group(id=bot.group), type=bot.role, identity=b)
                )
                return b
            else:
                raise UserHasNotPermissionError()
        else:
            raise UserHasNotPermissionError()

    # SADMIN, GADMIN (own group)
    def save_role(self, role: Role, params: RequestParameters) -> Role:
        if params.user and any(
            (
                params.user.is_site_admin(),
                params.user.is_group_admin(role.group),
            )
        ):
            return self.roles.save(role)
        else:
            raise UserHasNotPermissionError()

    # SADMIN, GADMIN (own group)
    def get_group(self, id: str, params: RequestParameters) -> Optional[Group]:
        group = self.groups.get(id)
        if (
            group
            and params.user
            and any(
                (
                    params.user.is_site_admin(),
                    params.user.is_group_admin(group),
                )
            )
        ):
            return group
        else:
            raise GroupNotFoundError()

    # SADMIN, GADMIN (own group), USER (own user)
    def get_user(self, id: int, params: RequestParameters) -> Optional[User]:
        user = self.ldap.get(id) or self.users.get(id)
        if not user:
            raise UserNotFoundError()

        groups = [r.group for r in self.roles.get_all_by_user(user.id)]

        if params.user and any(
            (
                params.user.is_site_admin(),
                params.user.is_group_admin(groups),
                params.user.is_himself(user),
            )
        ):
            return user
        else:
            raise UserNotFoundError()

    # SADMIN, USER (owner)
    def get_bot(self, id: int, params: RequestParameters) -> Optional[User]:
        bot = self.bots.get(id)
        if (
            bot
            and params.user
            and any(
                (
                    params.user.is_site_admin(),
                    params.user.is_himself(user=Identity(id=bot.owner)),
                )
            )
        ):
            return bot
        else:
            raise UserHasNotPermissionError()

    # SADMIN, USER (owner)
    def get_all_bots_by_owner(
        self, owner: int, params: RequestParameters
    ) -> List[Bot]:
        if params.user and any(
            (
                params.user.is_site_admin(),
                params.user.is_himself(Identity(id=owner)),
            )
        ):
            return self.bots.get_all_by_owner(owner)
        else:
            raise UserHasNotPermissionError()

    def exists_bot(self, id: int) -> bool:
        return self.bots.exists(id)

    def authenticate(self, name: str, pwd: str) -> Optional[JWTUser]:
        user = self.ldap.login(name, pwd) or self.users.get_by_name(name)
        if user and user.password.check(pwd):  # type: ignore
            return self.get_jwt(user.id)
        return None

    def get_jwt(self, user_id: int) -> Optional[JWTUser]:
        user = self.ldap.get(user_id) or self.users.get(user_id)
        if user:
            return JWTUser(
                id=user.id,
                impersonator=user.get_impersonator(),
                type=user.type,
                groups=[
                    JWTGroup(id=r.group.id, name=r.group.name, role=r.type)
                    for r in self.roles.get_all_by_user(user_id)
                ],
            )

        return None

    # SADMIN
    def get_all_groups(self, params: RequestParameters) -> List[Group]:
        if params.user and params.user.is_site_admin():
            return self.groups.get_all()
        else:
            raise UserHasNotPermissionError()

    # SADMIN
    def get_all_users(self, params: RequestParameters) -> List[User]:
        if params.user and params.user.is_site_admin():
            return self.ldap.get_all() + self.users.get_all()
        else:
            raise UserHasNotPermissionError()

    # SADMIN
    def get_all_bots(self, params: RequestParameters) -> List[Bot]:
        if params.user and params.user.is_site_admin():
            return self.bots.get_all()
        else:
            raise UserHasNotPermissionError()

    # SADMIN, GADMIN (own group)
    def get_all_roles_in_group(
        self, group: str, params: RequestParameters
    ) -> List[Role]:
        if params.user and any(
            (
                params.user.is_site_admin(),
                params.user.is_group_admin(Group(id=group)),
            )
        ):
            return self.roles.get_all_by_group(group)
        else:
            raise UserHasNotPermissionError()

    # SADMIN, GADMIN (own group)
    def delete_group(self, id: str, params: RequestParameters) -> None:
        if params.user and any(
            (
                params.user.is_site_admin(),
                params.user.is_group_admin(Group(id=id)),
            )
        ):
            return self.groups.delete(id)
        else:
            raise UserHasNotPermissionError()

    # SADMIN, USER (own user)
    def delete_user(self, id: int, params: RequestParameters) -> None:
        if params.user and any(
            (params.user.is_site_admin(), params.user.is_himself(User(id=id)))
        ):
            for b in self.bots.get_all_by_owner(id):
                self.delete_bot(b.id, params)

            self.ldap.delete(id)
            return self.users.delete(id)  # return for test purpose

        else:
            raise UserHasNotPermissionError()

    # SADMIN, USER (owner)
    def delete_bot(self, id: int, params: RequestParameters) -> None:
        bot = self.bots.get(id)
        if (
            params.user
            and bot
            and any(
                (
                    params.user.is_site_admin(),
                    params.user.is_himself(Identity(id=bot.owner)),
                )
            )
        ):
            return self.bots.delete(id)
        else:
            raise UserHasNotPermissionError()

    # SADMIN, GADMIN (own group)
    def delete_role(
        self, user: int, group: str, params: RequestParameters
    ) -> None:
        if params.user and any(
            (
                params.user.is_site_admin(),
                params.user.is_group_admin(Group(id=group)),
            )
        ):
            return self.roles.delete(user, group)
        else:
            raise UserHasNotPermissionError()
