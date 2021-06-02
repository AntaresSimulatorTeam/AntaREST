import logging
from typing import Optional, List

from sqlalchemy import exists  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from antarest.common.config import Config
from antarest.common.roles import RoleType
from antarest.login.model import (
    User,
    Password,
    Group,
    Role,
    Identity,
    Bot,
    UserLdap,
)


class GroupRepository:
    """
    Database connector to manage Group entity.
    """

    def __init__(self, session: Session):
        self.session = session
        self.logger = logging.Logger(self.__class__.__name__)
        self.save(Group(id="admin", name="admin"))

    def save(self, group: Group) -> Group:
        res = self.session.query(exists().where(Group.id == group.id)).scalar()
        if res:
            self.session.merge(group)
        else:
            self.session.add(group)
        self.session.commit()

        self.logger.debug(f"Group {group.id} saved")
        return group

    def get(self, id: str) -> Optional[Group]:
        group: Group = self.session.query(Group).get(id)
        return group

    def get_by_name(self, name: str) -> Group:
        group: Group = self.session.query(Group).filter_by(name=name).first()
        return group

    def get_all(self) -> List[Group]:
        groups: List[Group] = self.session.query(Group).all()
        return groups

    def delete(self, id: str) -> None:
        g = self.session.query(Group).get(id)
        self.session.delete(g)
        self.session.commit()

        self.logger.debug(f"Group {id} deleted")


class UserRepository:
    """
    Database connector to manage User entity.
    """

    def __init__(self, config: Config, session: Session) -> None:
        self.session = session
        self.logger = logging.Logger(self.__class__.__name__)
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

        self.logger.debug(f"User {user.id} saved")
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

        self.logger.debug(f"User {id} deleted")


class UserLdapRepository:
    """
    Database connector to manage UserLdap entity.
    """

    def __init__(self, session: Session) -> None:
        self.session = session
        self.logger = logging.Logger(self.__class__.__name__)

    def save(self, user_ldap: UserLdap) -> UserLdap:
        res = self.session.query(
            exists().where(UserLdap.id == user_ldap.id)
        ).scalar()
        if res:
            self.session.merge(user_ldap)
        else:
            self.session.add(user_ldap)
        self.session.commit()

        self.logger.debug(f"User LDAP {user_ldap.id} saved")
        return user_ldap

    def get(self, id: int) -> Optional[UserLdap]:
        user_ldap: Optional[UserLdap] = self.session.query(UserLdap).get(id)
        return user_ldap

    def get_by_name(self, name: str) -> Optional[UserLdap]:
        user: UserLdap = (
            self.session.query(UserLdap).filter_by(name=name).first()
        )
        return user

    def get_all(self) -> List[UserLdap]:
        users_ldap: List[UserLdap] = self.session.query(UserLdap).all()
        return users_ldap

    def delete(self, id: int) -> None:
        u: UserLdap = self.session.query(UserLdap).get(id)
        self.session.delete(u)
        self.session.commit()

        self.logger.debug(f"User LDAP {id} deleted")


class BotRepository:
    """
    Database connector to manage Bot entity.
    """

    def __init__(self, session: Session) -> None:
        self.session = session
        self.logger = logging.Logger(self.__class__.__name__)

    def save(self, bot: Bot) -> Bot:
        res = self.session.query(exists().where(Bot.id == bot.id)).scalar()
        if res:
            raise ValueError("Bot already exist")
        else:
            self.session.add(bot)
        self.session.commit()

        self.logger.debug(f"Bot {bot.id} saved")
        return bot

    def get(self, id: int) -> Optional[Bot]:
        bot: Bot = self.session.query(Bot).get(id)
        return bot

    def get_all(self) -> List[Bot]:
        bots: List[Bot] = self.session.query(Bot).all()
        return bots

    def delete(self, id: int) -> None:
        u: Bot = self.session.query(Bot).get(id)
        self.session.delete(u)
        self.session.commit()

        self.logger.debug(f"Bot {id} deleted")

    def get_all_by_owner(self, owner: int) -> List[Bot]:
        bots: List[Bot] = self.session.query(Bot).filter_by(owner=owner).all()
        return bots

    def exists(self, id: int) -> bool:
        res: bool = self.session.query(exists().where(Bot.id == id)).scalar()
        return res


class RoleRepository:
    """
    Database connector to manage Role entity.
    """

    def __init__(self, session: Session):
        self.session = session
        self.logger = logging.Logger(self.__class__.__name__)
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

        self.logger.debug(
            f"Role (user={role.identity}, group={role.group} saved"
        )
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

        self.logger.debug(f"Role (user={user}, group={group} deleted")
