# Copyright (c) 2025, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import logging
from typing import List, Optional

from sqlalchemy import exists  # type: ignore
from sqlalchemy.orm import Session, joinedload  # type: ignore

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.login.model import Bot, Group, Identity, Role, User, UserLdap

logger = logging.getLogger(__name__)


class GroupRepository:
    """
    Database connector to manage Group entity.
    """

    def __init__(
        self,
        session: Optional[Session] = None,
    ) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        """Get the SqlAlchemy session or create a new one on the fly if not available in the current thread."""
        if self._session is None:
            return db.session
        return self._session

    def save(self, group: Group) -> Group:
        res = self.session.query(exists().where(Group.id == group.id)).scalar()
        if res:
            self.session.merge(group)
        else:
            self.session.add(group)
        self.session.commit()

        logger.debug(f"Group {group.id} saved")
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

        logger.debug(f"Group {id} deleted")


class IdentityRepository:
    """
    Database connector to manage Identity table.
    """

    def __init__(
        self,
        session: Optional[Session] = None,
    ) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        """Get the SqlAlchemy session or create a new one on the fly if not available in the current thread."""
        if self._session is None:
            return db.session
        return self._session

    def get_all_users(self) -> list[Identity]:
        identities: list[Identity] = self.session.query(Identity).where(Identity.type != "bots").all()
        return identities


class UserRepository:
    """
    Database connector to manage User entity.
    """

    def __init__(
        self,
        session: Optional[Session] = None,
    ) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        """Get the SqlAlchemy session or create a new one on the fly if not available in the current thread."""
        if self._session is None:
            return db.session
        return self._session

    def save(self, user: User) -> User:
        res = self.session.query(exists().where(User.id == user.id)).scalar()
        if res:
            self.session.merge(user)
        else:
            self.session.add(user)
        self.session.commit()

        logger.debug(f"User {user.id} saved")
        return user

    def get(self, id_number: int) -> Optional[User]:
        user: User = self.session.query(User).get(id_number)
        return user

    def get_by_name(self, name: str) -> Optional[User]:
        user: User = self.session.query(User).filter_by(name=name).first()
        return user

    def delete(self, id: int) -> None:
        u: User = self.session.query(User).get(id)
        self.session.delete(u)
        self.session.commit()

        logger.debug(f"User {id} deleted")


class UserLdapRepository:
    """
    Database connector to manage UserLdap entity.
    """

    def __init__(
        self,
        session: Optional[Session] = None,
    ) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        """Get the SqlAlchemy session or create a new one on the fly if not available in the current thread."""
        if self._session is None:
            return db.session
        return self._session

    def save(self, user_ldap: UserLdap) -> UserLdap:
        res = self.session.query(exists().where(UserLdap.id == user_ldap.id)).scalar()
        if res:
            self.session.merge(user_ldap)
        else:
            self.session.add(user_ldap)
        self.session.commit()

        logger.debug(f"User LDAP {user_ldap.id} saved")
        return user_ldap

    def get(self, id_number: int) -> Optional[UserLdap]:
        user_ldap: Optional[UserLdap] = self.session.query(UserLdap).get(id_number)
        return user_ldap

    def get_by_name(self, name: str) -> Optional[UserLdap]:
        user: UserLdap = self.session.query(UserLdap).filter_by(name=name).first()
        return user

    def get_by_external_id(self, external_id: str) -> Optional[UserLdap]:
        user: UserLdap = self.session.query(UserLdap).filter_by(external_id=external_id).first()
        return user

    def delete(self, id_number: int) -> None:
        u: UserLdap = self.session.query(UserLdap).get(id_number)
        self.session.delete(u)
        self.session.commit()

        logger.debug(f"User LDAP {id_number} deleted")


class BotRepository:
    """
    Database connector to manage Bot entity.
    """

    def __init__(
        self,
        session: Optional[Session] = None,
    ) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        """Get the SqlAlchemy session or create a new one on the fly if not available in the current thread."""
        if self._session is None:
            return db.session
        return self._session

    def save(self, bot: Bot) -> Bot:
        res = self.session.query(exists().where(Bot.id == bot.id)).scalar()
        if res:
            raise ValueError("Bot already exist")
        else:
            self.session.add(bot)
        self.session.commit()

        logger.debug(f"Bot {bot.id} saved")
        return bot

    def get(self, id_number: int) -> Optional[Bot]:
        bot: Bot = self.session.query(Bot).get(id_number)
        return bot

    def get_all(
        self,
    ) -> List[Bot]:
        bots: List[Bot] = self.session.query(Bot).all()
        return bots

    def delete(self, id_number: int) -> None:
        u: Bot = self.session.query(Bot).get(id_number)
        self.session.delete(u)
        self.session.commit()

        logger.debug(f"Bot {id_number} deleted")

    def get_all_by_owner(self, owner: int) -> List[Bot]:
        bots: List[Bot] = self.session.query(Bot).filter_by(owner=owner).all()
        return bots

    def get_by_name_and_owner(self, owner: int, name: str) -> Optional[Bot]:
        bot: Bot = self.session.query(Bot).filter_by(owner=owner, name=name).first()
        return bot

    def exists(self, id_number: int) -> bool:
        res: bool = self.session.query(exists().where(Bot.id == id_number)).scalar()
        return res


class RoleRepository:
    """
    Database connector to manage Role entity.
    """

    def __init__(
        self,
        session: Optional[Session] = None,
    ) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        """Get the SqlAlchemy session or create a new one on the fly if not available in the current thread."""
        if self._session is None:
            return db.session
        return self._session

    def save(self, role: Role) -> Role:
        role.group = self.session.merge(role.group)
        role.identity = self.session.merge(role.identity)

        self.session.add(role)
        self.session.commit()

        logger.debug(f"Role (user={role.identity}, group={role.group} saved")
        return role

    def get(self, user: int, group: str) -> Optional[Role]:
        role: Role = self.session.query(Role).get((user, group))
        return role

    def get_all(self, details: bool, groups: Optional[list[Group]] = None) -> list[Role]:
        q = self.session.query(Role)
        q = q.join(Role.identity).options(joinedload(Role.identity)).where(Identity.type != "bots")

        if details:
            q = q.options(joinedload(Role.group))

        if groups:
            group_mapping = [group.id for group in groups]
            q = q.filter(Role.group_id.in_(group_mapping))

        roles: list[Role] = q.all()
        return roles

    def get_all_by_user(self, /, user_id: int) -> List[Role]:
        """
        Get all roles (and groups) associated to a user.

        Args:
            user_id: The user identifier.

        Returns:
            A list of `Role` objects.
        """
        # When we fetch the list of roles, we also need to fetch the associated groups.
        # We use a SQL query with joins to fetch all these data efficiently.
        stm = self.session.query(Role).options(joinedload(Role.group)).filter_by(identity_id=user_id)
        roles: List[Role] = stm.all()
        return roles

    def get_all_by_group(self, group: str) -> List[Role]:
        roles: List[Role] = self.session.query(Role).filter_by(group_id=group).all()
        return roles

    def delete(self, user: int, group: str) -> None:
        r = self.session.query(Role).get((user, group))
        self.session.delete(r)
        self.session.commit()

        logger.debug(f"Role (user={user}, group={group} deleted")
