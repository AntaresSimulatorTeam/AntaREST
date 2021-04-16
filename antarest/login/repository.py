from typing import Optional, List

from sqlalchemy import exists  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from antarest.common.config import Config
from antarest.common.roles import RoleType
from antarest.login.model import User, Password, Group, Role, Identity


class GroupRepository:
    def __init__(self, session: Session):
        self.session = session
        self.save(Group(id="admin", name="admin"))

    def save(self, group: Group) -> Group:
        res = self.session.query(exists().where(Group.id == group.id)).scalar()
        if res:
            self.session.merge(group)
        else:
            self.session.add(group)
        self.session.commit()
        return group

    def get(self, id: str) -> Optional[Group]:
        group: Group = self.session.query(Group).get(id)
        return group

    def get_all(self) -> List[Group]:
        groups: List[Group] = self.session.query(Group).all()
        return groups

    def delete(self, id: str) -> None:
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
                    id=1,
                    name="admin",
                    password=Password(config.security.admin_pwd),
                )
            )
        elif not admin_user.password.check(config.security.admin_pwd):  # type: ignore
            admin_user.password = Password(config.security.admin_pwd)  # type: ignore
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


class RoleRepository:
    def __init__(self, session: Session):
        self.session = session
        if self.get(1, "admin") is None:
            self.save(
                Role(
                    type=RoleType.ADMIN,
                    identity=User(id=1),
                    group=Group(id="admin"),
                )
            )

    def save(self, role: Role) -> Role:
        role.group = self.session.merge(role.group)
        role.identity = self.session.merge(role.identity)

        self.session.add(role)
        self.session.commit()
        return role

    def get(self, user: int, group: str) -> Optional[Role]:
        role: Role = self.session.query(Role).get((user, group))
        return role

    def get_all_by_user(self, user: int) -> List[Role]:
        roles: List[Role] = (
            self.session.query(Role).filter_by(identity_id=user).all()
        )
        return roles

    def get_all_by_group(self, group: str) -> List[Role]:
        roles: List[Role] = (
            self.session.query(Role).filter_by(group_id=group).all()
        )
        return roles

    def delete(self, user: int, group: str) -> None:
        r = self.session.query(Role).get((user, group))
        self.session.delete(r)
        self.session.commit()
