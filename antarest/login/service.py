from typing import Optional, List

from antarest.common.custom_types import JSON
from antarest.common.interfaces.eventbus import IEventBus
from antarest.common.jwt import JWTUser, JWTGroup
from antarest.login.model import User, Group, Role
from antarest.login.repository import (
    UserRepository,
    GroupRepository,
    RoleRepository,
)


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
    def save_group(self, group: Group) -> Group:
        return self.groups.save(group)

    # SADMIN, USER (own user)
    def save_user(self, user: User) -> User:
        return self.users.save(user)

    # SADMIN, GADMIN (own group)
    def save_role(self, role: Role) -> Role:
        return self.roles.save(role)

    # SADMIN, GADMIN (own group)
    def get_group(self, id: str) -> Optional[Group]:
        return self.groups.get(id)

    # SADMIN, GADMIN (own group), USER (own user)
    def get_user(self, id: int) -> Optional[User]:
        return self.users.get(id)

    def authenticate(self, name: str, pwd: str) -> Optional[JWTUser]:
        user = self.users.get_by_name(name)
        if user and user.password.check(pwd):
            return self.get_jwt(user.id)

    def get_jwt(self, user_id: int) -> Optional[JWTUser]:
        user = self.get_user(user_id)
        if user:
            return JWTUser(
                id=user.id,
                name=user.name,
                groups=[
                    JWTGroup(id=r.group.id, name=r.group.name, role=r.type)
                    for r in self.get_all_roles(user=user_id)
                ],
            )

    # SADMIN
    def get_all_groups(self) -> List[Group]:
        return self.groups.get_all()

    # SADMIN
    def get_all_users(self) -> List[User]:
        return self.users.get_all()

    # SADMIN, GADMIN (own group)
    def get_all_roles(
        self, user: Optional[int] = None, group: Optional[str] = None
    ) -> List[Role]:
        if user is None and group is not None:
            return self.roles.get_all_by_group(group)
        if user is not None and group is None:
            return self.roles.get_all_by_user(user)

        raise ValueError("choice either user or group not both or none")

    # SADMIN, GADMIN (own group)
    def delete_group(self, id: str) -> None:
        return self.groups.delete(id)

    # SADMIN, USER (own user)
    def delete_user(self, id: int) -> None:
        return self.users.delete(id)

    # SADMIN, GADMIN (own group)
    def delete_role(self, user: int, group: str) -> None:
        return self.roles.delete(user, group)
