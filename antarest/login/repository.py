from typing import Optional, List

from sqlalchemy import exists  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from antarest.common.config import Config
from antarest.login.model import User, Role, Password, Group


class GroupRepository:
    def __init__(self, config: Config, session: Session):
        self.session = session

    def save(self, group: Group) -> Group:
        res = self.session.query(exists().where(Group.id == group.id)).scalar()
        if res:
            self.session.merge(group)
        else:
            self.session.add(group)
        self.session.commit()
        return group

    def get(self, id: int) -> Optional[Group]:
        group: Group = self.session.query(Group).get(id)
        return group

    def get_all(self) -> List[Group]:
        groups: List[Group] = self.session.query(Group).all()
        return groups

    def delete(self, id: int) -> None:
        g = self.session.query(Group).get(id)
        self.session.delete(g)
        self.session.commit()


class UserRepository:
    def __init__(self, config: Config, session: Session) -> None:
        self.session = session
        # init seed admin user from conf
        admin_user = self.get_by_name("admin")
        if admin_user is None:
            self.save(
                User(
                    name="admin",
                    role=Role.ADMIN,
                    password=Password(config["security.login.admin.pwd"]),
                )
            )
            self.save(
                User(name="alice", role=Role.USER, password=Password("alice"))
            )
            self.save(
                User(name="bob", role=Role.USER, password=Password("bob"))
            )
        elif not admin_user.password.check(config["security.login.admin.pwd"]):  # type: ignore
            admin_user.password = Password(config["security.login.admin.pwd"])  # type: ignore
            self.save(admin_user)

    def save(self, user: User) -> User:
        res = self.session.query(exists().where(User.id == user.id)).scalar()
        if res:
            self.session.merge(user)
        else:
            self.session.add(user)
        self.session.commit()
        return user

    def get(self, id: int) -> Optional[User]:
        user: User = self.session.query(User).get(id)
        return user

    def get_by_name(self, name: str) -> User:
        user: User = self.session.query(User).filter_by(name=name).first()
        return user

    def get_all(self) -> List[User]:
        users: List[User] = self.session.query(User).all()
        return users

    def delete(self, id: int) -> None:
        u: User = self.session.query(User).get(id)
        self.session.delete(u)
        self.session.commit()
