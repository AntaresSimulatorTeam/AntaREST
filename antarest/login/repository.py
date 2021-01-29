import uuid
from typing import Dict, Optional, List

from antarest.login.model import User, Role


class UserRepository:
    def __init__(self) -> None:
        self.users: Dict[int, User] = {
            0: User(id=0, name="admin", pwd="admin", role=Role.ADMIN)
        }

    def save(self, user: User) -> User:
        if user.id is None:
            user.id = uuid.uuid4().int
        self.users[user.id] = user
        return user

    def get(self, id: int) -> Optional[User]:
        return self.users.get(id)

    def get_by_name(self, name: str) -> User:
        return [u for u in self.users.values() if u.name == name][0]

    def get_all(self) -> List[User]:
        return list(self.users.values())

    def delete(self, id: int) -> None:
        if id in self.users:
            del self.users[id]
