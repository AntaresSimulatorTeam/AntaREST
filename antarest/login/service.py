from typing import Optional, List

import werkzeug as werkzeug

from antarest.common.custom_types import JSON
from antarest.common.interfaces.eventbus import IEventBus
from antarest.common.jwt import JWTUser, JWTGroup
from antarest.common.requests import (
    RequestParameters,
    UserHasNotPermissionError,
)
from antarest.login.model import User, Group, Role
from antarest.login.repository import (
    UserRepository,
    GroupRepository,
    RoleRepository,
)


class GroupNotFoundError(werkzeug.exceptions.NotFound):
    pass


class UserNotFoundError(werkzeug.exceptions.NotFound):
    pass


class LoginService:
    def __init__(
        self,
        user_repo: UserRepository,
        group_repo: GroupRepository,
        role_repo: RoleRepository,
        event_bus: IEventBus,
    ):
        self.users = user_repo
        self.groups = group_repo
        self.roles = role_repo
        self.event_bus = event_bus

    # SADMIN, GADMIN (own group)
    def save_group(self, group: Group, params: RequestParameters) -> Group:
        if params.user and any(
            (params.user.is_site_admin(), params.user.is_group_admin(group))
        ):
            return self.groups.save(group)
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
        user = self.users.get(id)
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

    def authenticate(self, name: str, pwd: str) -> Optional[JWTUser]:
        user = self.users.get_by_name(name)
        if user and user.password.check(pwd):  # type: ignore
            return self.get_jwt(user.id)
        return None

    def get_jwt(self, user_id: int) -> Optional[JWTUser]:
        user = self.users.get(user_id)
        if user:
            return JWTUser(
                id=user.id,
                name=user.name,
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
            return self.users.get_all()
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
            return self.users.delete(id)
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
