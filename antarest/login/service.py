from typing import Optional, List

from antarest.common.custom_types import JSON
from antarest.common.interfaces.eventbus import IEventBus
from antarest.login.model import User, Group
from antarest.login.repository import UserRepository, GroupRepository


class LoginService:
    def __init__(
        self,
        user_repo: UserRepository,
        group_repo: GroupRepository,
        event_bus: IEventBus,
    ):
        self.users = user_repo
        self.groups = group_repo
        self.event_bus = event_bus

    def save_group(self, group: Group) -> Group:
        return self.groups.save(group)

    def save_user(self, user: User) -> User:
        return self.users.save(user)

    def get_group(self, id: int) -> Optional[Group]:
        return self.groups.get(id)

    def get_user(self, id: int) -> Optional[User]:
        return self.users.get(id)

    def authenticate(self, name: str, pwd: str) -> Optional[User]:
        user = self.users.get_by_name(name)
        return user if user and user.password.check(pwd) else None  # type: ignore

    def identify(self, payload: JSON) -> Optional[User]:
        return self.get_user(payload["identity"])

    def get_all_groups(self) -> List[Group]:
        return self.groups.get_all()

    def get_all_users(self) -> List[User]:
        return self.users.get_all()

    def delete_group(self, id: int) -> None:
        return self.groups.delete(id)

    def delete_user(self, id: int) -> None:
        self.users.delete(id)
