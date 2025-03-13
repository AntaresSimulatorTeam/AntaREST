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

from sqlalchemy import exists
from sqlalchemy.orm import Session, joinedload

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.login.model import Bot, Group, Role, User, UserLdap

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
        return self.session.get(Group, id)

    def get_by_name(self, name: str) -> Optional[Group]:
        return self.session.query(Group).filter_by(name=name).first()

    def get_all(self) -> List[Group]:
        return self.session.query(Group).all()

    def delete(self, id: str) -> None:
        g = self.session.query(Group).get(id)
        self.session.delete(g)
        self.session.commit()

        logger.debug(f"Group {id} deleted")


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
        return self.session.get(User, id_number)

    def get_by_name(self, name: str) -> Optional[User]:
        return self.session.query(User).filter_by(name=name).first()

    def get_all(self) -> List[User]:
        return self.session.query(User).all()

    def delete(self, id: int) -> None:
        self.session.query(User).filter(User.id == id).delete(synchronize_session=False)
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
        return self.session.query(UserLdap).get(id_number)

    def get_by_name(self, name: str) -> Optional[UserLdap]:
        return self.session.query(UserLdap).filter_by(name=name).first()

    def get_by_external_id(self, external_id: str) -> Optional[UserLdap]:
        return self.session.query(UserLdap).filter_by(external_id=external_id).first()

    def get_all(
        self,
    ) -> List[UserLdap]:
        return self.session.query(UserLdap).all()

    def delete(self, id_number: int) -> None:
        self.session.query(UserLdap).filter(UserLdap.id == id_number).delete(synchronize_session=False)
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
        return self.session.query(Bot).get(id_number)

    def get_all(
        self,
    ) -> List[Bot]:
        return self.session.query(Bot).all()

    def delete(self, id_number: int) -> None:
        self.session.query(Bot).filter(Bot.id == id_number).delete(synchronize_session=False)
        self.session.commit()

        logger.debug(f"Bot {id_number} deleted")

    def get_all_by_owner(self, owner: int) -> List[Bot]:
        return self.session.query(Bot).filter_by(owner=owner).all()

    def get_by_name_and_owner(self, owner: int, name: str) -> Optional[Bot]:
        return self.session.query(Bot).filter_by(owner=owner, name=name).first()

    def exists(self, id_number: int) -> bool:
        return self.session.query(exists().where(Bot.id == id_number)).scalar() is not None


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
        return self.session.query(Role).get((user, group))

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
