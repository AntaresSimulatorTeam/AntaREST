import logging
from typing import Optional, List

from sqlalchemy import exists  # type: ignore

from antarest.core.config import Config
from antarest.core.jwt import ADMIN_ID
from antarest.core.roles import RoleType
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.login.model import (
    User,
    Password,
    Group,
    Role,
    Bot,
    UserLdap,
)

logger = logging.getLogger(__name__)


class GroupRepository:
    """
    Database connector to manage Group entity.
    """

    def __init__(self) -> None:
        with db():
            self.save(Group(id="admin", name="admin"))

    def save(self, group: Group) -> Group:
        res = db.session.query(exists().where(Group.id == group.id)).scalar()
        if res:
            db.session.merge(group)
        else:
            db.session.add(group)
        db.session.commit()

        logger.debug(f"Group {group.id} saved")
        return group

    def get(self, id: str) -> Optional[Group]:
        group: Group = db.session.query(Group).get(id)
        return group

    def get_by_name(self, name: str) -> Group:
        group: Group = db.session.query(Group).filter_by(name=name).first()
        return group

    def get_all(self) -> List[Group]:
        groups: List[Group] = db.session.query(Group).all()
        return groups

    def delete(self, id: str) -> None:
        g = db.session.query(Group).get(id)
        db.session.delete(g)
        db.session.commit()

        logger.debug(f"Group {id} deleted")


class UserRepository:
    """
    Database connector to manage User entity.
    """

    def __init__(self, config: Config) -> None:
        # init seed admin user from conf
        with db():
            admin_user = self.get_by_name("admin")
            if admin_user is None:
                self.save(
                    User(
                        id=ADMIN_ID,
                        name="admin",
                        password=Password(config.security.admin_pwd),
                    )
                )
            elif not admin_user.password.check(config.security.admin_pwd):  # type: ignore
                admin_user.password = Password(config.security.admin_pwd)  # type: ignore
                self.save(admin_user)

    def save(self, user: User) -> User:
        res = db.session.query(exists().where(User.id == user.id)).scalar()
        if res:
            db.session.merge(user)
        else:
            db.session.add(user)
        db.session.commit()

        logger.debug(f"User {user.id} saved")
        return user

    def get(self, id: int) -> Optional[User]:
        user: User = db.session.query(User).get(id)
        return user

    def get_by_name(self, name: str) -> User:
        user: User = db.session.query(User).filter_by(name=name).first()
        return user

    def get_all(self) -> List[User]:
        users: List[User] = db.session.query(User).all()
        return users

    def delete(self, id: int) -> None:
        u: User = db.session.query(User).get(id)
        db.session.delete(u)
        db.session.commit()

        logger.debug(f"User {id} deleted")


class UserLdapRepository:
    """
    Database connector to manage UserLdap entity.
    """

    def save(self, user_ldap: UserLdap) -> UserLdap:
        res = db.session.query(
            exists().where(UserLdap.id == user_ldap.id)
        ).scalar()
        if res:
            db.session.merge(user_ldap)
        else:
            db.session.add(user_ldap)
        db.session.commit()

        logger.debug(f"User LDAP {user_ldap.id} saved")
        return user_ldap

    def get(self, id: int) -> Optional[UserLdap]:
        user_ldap: Optional[UserLdap] = db.session.query(UserLdap).get(id)
        return user_ldap

    def get_by_name(self, name: str) -> Optional[UserLdap]:
        user: UserLdap = (
            db.session.query(UserLdap).filter_by(name=name).first()
        )
        return user

    def get_by_external_id(self, external_id: str) -> Optional[UserLdap]:
        user: UserLdap = (
            db.session.query(UserLdap)
            .filter_by(external_id=external_id)
            .first()
        )
        return user

    def get_all(self) -> List[UserLdap]:
        users_ldap: List[UserLdap] = db.session.query(UserLdap).all()
        return users_ldap

    def delete(self, id: int) -> None:
        u: UserLdap = db.session.query(UserLdap).get(id)
        db.session.delete(u)
        db.session.commit()

        logger.debug(f"User LDAP {id} deleted")


class BotRepository:
    """
    Database connector to manage Bot entity.
    """

    def save(self, bot: Bot) -> Bot:
        res = db.session.query(exists().where(Bot.id == bot.id)).scalar()
        if res:
            raise ValueError("Bot already exist")
        else:
            db.session.add(bot)
        db.session.commit()

        logger.debug(f"Bot {bot.id} saved")
        return bot

    def get(self, id: int) -> Optional[Bot]:
        bot: Bot = db.session.query(Bot).get(id)
        return bot

    def get_all(self) -> List[Bot]:
        bots: List[Bot] = db.session.query(Bot).all()
        return bots

    def delete(self, id: int) -> None:
        u: Bot = db.session.query(Bot).get(id)
        db.session.delete(u)
        db.session.commit()

        logger.debug(f"Bot {id} deleted")

    def get_all_by_owner(self, owner: int) -> List[Bot]:
        bots: List[Bot] = db.session.query(Bot).filter_by(owner=owner).all()
        return bots

    def get_by_name_and_owner(self, owner: int, name: str) -> Optional[Bot]:
        bot: Bot = (
            db.session.query(Bot).filter_by(owner=owner, name=name).first()
        )
        return bot

    def exists(self, id: int) -> bool:
        res: bool = db.session.query(exists().where(Bot.id == id)).scalar()
        return res


class RoleRepository:
    """
    Database connector to manage Role entity.
    """

    def __init__(self) -> None:
        with db():
            if self.get(1, "admin") is None:
                self.save(
                    Role(
                        type=RoleType.ADMIN,
                        identity=User(id=1),
                        group=Group(id="admin"),
                    )
                )

    def save(self, role: Role) -> Role:
        role.group = db.session.merge(role.group)
        role.identity = db.session.merge(role.identity)

        db.session.add(role)
        db.session.commit()

        logger.debug(f"Role (user={role.identity}, group={role.group} saved")
        return role

    def get(self, user: int, group: str) -> Optional[Role]:
        role: Role = db.session.query(Role).get((user, group))
        return role

    def get_all_by_user(self, user: int) -> List[Role]:
        roles: List[Role] = (
            db.session.query(Role).filter_by(identity_id=user).all()
        )
        return roles

    def get_all_by_group(self, group: str) -> List[Role]:
        roles: List[Role] = (
            db.session.query(Role).filter_by(group_id=group).all()
        )
        return roles

    def delete(self, user: int, group: str) -> None:
        r = db.session.query(Role).get((user, group))
        db.session.delete(r)
        db.session.commit()

        logger.debug(f"Role (user={user}, group={group} deleted")
