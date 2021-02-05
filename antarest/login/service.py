from typing import Optional, List

from antarest.common.custom_types import JSON
from antarest.login.model import User
from antarest.login.repository import UserRepository


class LoginService:
    def __init__(self, user_repo: UserRepository):
        self.repo = user_repo

    def save(self, user: User) -> User:
        return self.repo.save(user)

    def get(self, id: int) -> Optional[User]:
        return self.repo.get(id)

    def authenticate(self, name: str, pwd: str) -> Optional[User]:
        user = self.repo.get_by_name(name)
        return user if user and user.password.check(pwd) else None  # type: ignore

    def identify(self, payload: JSON) -> Optional[User]:
        return self.get(payload["identity"])

    def get_all(self) -> List[User]:
        return self.repo.get_all()

    def delete(self, id: int) -> None:
        self.repo.delete(id)
