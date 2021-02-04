import uuid
from typing import Dict, Optional, List

from sqlalchemy.orm import Session

from antarest.common.config import Config
from antarest.login.model import User, Role


class UserRepository:
    def __init__(self, config: Config, db: Session) -> None:
        # self.users: Dict[int, User] = {
        #     0: User(
        #         name="admin",
        #         pwd=config["login.admin.pwd"],
        #         role=Role.ADMIN,
        #     )
        # }

        self.db = db

    def save(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        return user

    def get(self, id: int) -> Optional[User]:
        user: User = self.db.query(User).get(id)
        return user

    def get_by_name(self, name: str) -> User:
        user: User = self.db.query(User).filter_by(name=name).first()
        return user

    def get_all(self) -> List[User]:
        users: List[User] = self.db.query(User).all()
        return users

    def delete(self, id: int) -> None:
        u = self.get(id)
        self.db.delete(u)
        self.db.commit()
