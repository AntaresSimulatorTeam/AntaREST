import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

try:
    # `httpx` is a modern alternative to the `requests` library
    import httpx as requests
except ImportError:
    # noinspection PyUnresolvedReferences, PyPackageRequirements
    import requests

from antarest.core.config import Config
from antarest.core.model import JSON
from antarest.login.model import Group, Role, UserLdap
from antarest.login.repository import GroupRepository, RoleRepository, UserLdapRepository

logger = logging.getLogger(__name__)


@dataclass
class AuthDTO:
    """
    Input LDAP data
    """

    user: str
    password: str

    @staticmethod
    def from_json(data: JSON) -> "AuthDTO":
        return AuthDTO(user=data["user"], password=data["password"])

    def to_json(self) -> JSON:
        return {"user": self.user, "password": self.password}


@dataclass
class ExternalUser:
    """
    Output LDAP data
    """

    external_id: str
    first_name: str
    last_name: str
    groups: Dict[str, str]

    @staticmethod
    def from_json(id: str, data: JSON) -> "ExternalUser":
        return ExternalUser(
            external_id=id,
            first_name=data["firstName"],
            last_name=data["lastName"],
            groups=data.get("groups", {}),
        )

    def to_json(self) -> JSON:
        return {
            "externalId": self.external_id,
            "firstName": self.first_name,
            "lastName": self.last_name,
            "groups": self.groups,
        }


class LdapService:
    """
    LDAP facade with connector to ldap server
    """

    def __init__(
        self,
        config: Config,
        users: UserLdapRepository,
        groups: GroupRepository,
        roles: RoleRepository,
    ):
        self.url = config.security.external_auth.url
        self.group_mapping = config.security.external_auth.group_mapping
        self.add_ext_groups = config.security.external_auth.add_ext_groups
        self.users = users
        self.groups = groups
        self.roles = roles
        self.default_role_sync = config.security.external_auth.default_group_role

    def _fetch(self, name: str, password: str) -> Optional[ExternalUser]:
        """
        Fetch user from LDAP
        Args:
            name: username
            password: password

        Returns: User if connection success other Noen

        """
        if not self.url:
            return None

        auth = AuthDTO(user=name, password=password)
        try:
            res = requests.post(url=f"{self.url}/auth", json=auth.to_json())
        except Exception as e:
            logger.warning(
                "Failed to retrieve user from external auth service",
                exc_info=e,
            )
            return None
        if res.status_code != 200:
            return None

        return ExternalUser.from_json(name, res.json())

    def _save_or_update(self, user: ExternalUser) -> UserLdap:
        """
        Save user in db
        Args:
            user: user to save

        Returns:

        """
        existing_user = self.users.get_by_external_id(user.external_id)
        if not existing_user:
            existing_user = self.users.save(
                UserLdap(
                    name=f"{user.first_name} {user.last_name}",
                    external_id=user.external_id,
                    firstname=user.first_name,
                    lastname=user.last_name,
                )
            )

        existing_roles = self.roles.get_all_by_user(existing_user.id)

        mapped_groups = [
            Group(
                id=self.group_mapping.get(group_id, group_id),
                name=user.groups[group_id],
            )
            for group_id in user.groups
            if self.add_ext_groups or group_id in self.group_mapping.keys()
        ]
        grouprole_to_add = [
            (group.id, (self.groups.get(group.id) or group).name)
            for group in mapped_groups
            if group.id not in [role.group_id for role in existing_roles]
        ]
        logger.info(f"Saving new groups from external user {grouprole_to_add} from received {user.groups}")
        for group_id, group_name in grouprole_to_add:
            logger.info(
                "Adding user %s role %s to group %s (%s) following ldap sync",
                existing_user.name,
                self.default_role_sync.name,
                group_id,
                group_name,
            )
            group = self.groups.save(Group(id=group_id, name=group_name))
            self.roles.save(
                Role(
                    identity=existing_user,
                    group=group,
                    type=self.default_role_sync,
                )
            )

        return existing_user

    def get(self, id: int) -> Optional[UserLdap]:
        """
        Get User stored in DB
        Args:
            id: user id

        Returns: user

        """
        return self.users.get(id)

    def login(self, name: str, password: str) -> Optional[UserLdap]:
        """
        Try to log user to external LDAP
        Args:
            name: username
            password: password

        Returns: if logging success return a UserLDAP other None

        """
        user = self._fetch(name, password)
        if not user:
            return None

        return self._save_or_update(user)

    def get_all(self) -> List[UserLdap]:
        """
        Get all users in DB.

        Returns: list of users

        """
        return self.users.get_all()

    def delete(self, id: int) -> None:
        """
        Delete user
        Args:
            id: user id to delete

        Returns:

        """
        return self.users.delete(id)
