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

import datetime
import enum
from typing import List, Optional, Sequence, Tuple, cast

from pydantic import NonNegativeInt
from sqlalchemy import and_, delete, exists, func, not_, or_, select, sql
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Query, Session, joinedload, with_polymorphic

from antarest.core.interfaces.cache import ICache
from antarest.core.jwt import JWTUser
from antarest.core.model import PublicMode
from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.login.model import Group
from antarest.login.utils import get_current_user
from antarest.study.model import DEFAULT_WORKSPACE_NAME, Directory, RawStudy, Study, StudyAdditionalData, Tag


def escape_like(string: str, escape_char: str = "\\") -> str:
    """
    Escape the string parameter used in SQL LIKE expressions.

    Examples::

        from sqlalchemy_utils import escape_like

        query = session.query(User).filter(User.name.ilike(escape_like("John")))

    Args:
        string: a string to escape
        escape_char: escape character

    Returns:
        Escaped string.
    """
    return string.replace(escape_char, escape_char * 2).replace("%", escape_char + "%").replace("_", escape_char + "_")


class AccessPermissions(AntaresBaseModel, frozen=True, extra="forbid"):
    """
    This class object is build to pass on the user identity and its associated groups information
    into the listing function get_all below
    """

    is_admin: bool = False
    user_id: Optional[int] = None
    user_groups: Sequence[str] = ()

    @classmethod
    def for_current_user(cls) -> "AccessPermissions":
        """
        This function makes it easier to pass on user ids and groups into the repository filtering function by
        extracting the associated `AccessPermissions` object.
        """
        return cls.for_user(get_current_user())

    @classmethod
    def for_user(cls, user: Optional[JWTUser]) -> "AccessPermissions":
        """
        This function makes it easier to pass on user ids and groups into the repository filtering function by
        extracting the associated `AccessPermissions` object.

        Args:
            user: `JWTUser` holding user ids and groups

        Returns: `AccessPermissions`

        """
        if user:
            return cls(
                is_admin=user.is_site_admin() or user.is_admin_token(),
                user_id=user.id,
                user_groups=[group.id for group in user.groups],
            )
        else:
            return cls()


class StudyFilter(AntaresBaseModel, frozen=True, extra="forbid"):
    """Study filter class gathering the main filtering parameters

    Attributes:
        name: optional name regex of the study to match
        managed: indicate if just managed studies should be retrieved
        archived: optional if the study is archived
        variant: optional if the study is raw study
        versions: versions to filter by
        users: users to filter by
        groups: groups to filter by
        tags: tags to filter by
        study_ids: study IDs to filter by
        exists: if raw study missing
        workspace: optional workspace of the study
        folder: optional folder prefix of the study
        directory_id: optional directory ID to filter studies by
        access_permissions: query user ID, groups and admins status
    """

    name: str = ""
    managed: Optional[bool] = None
    archived: Optional[bool] = None
    variant: Optional[bool] = None
    versions: Sequence[str] = ()
    users: Sequence[int] = ()
    groups: Sequence[str] = ()
    tags: Sequence[str] = ()
    study_ids: Sequence[str] = ()
    exists: Optional[bool] = None
    workspace: str = ""
    folder: str = ""
    directory_id: str = ""
    access_permissions: AccessPermissions = AccessPermissions()


class StudySortBy(enum.StrEnum):
    """How to sort the results of studies query results"""

    NAME_ASC = "+name"
    NAME_DESC = "-name"
    DATE_ASC = "+date"
    DATE_DESC = "-date"


class StudyPagination(AntaresBaseModel, frozen=True, extra="forbid"):
    """
    Pagination of a studies query results

    Attributes:
        page_nb: offset
        page_size: SQL limit
    """

    page_nb: NonNegativeInt = 0
    page_size: NonNegativeInt = 0


class StudyMetadataRepository:
    """
    Database connector to manage Study entity
    """

    def __init__(self, cache_service: ICache, session: Optional[Session] = None):
        """
        Initialize the repository.

        Args:
            cache_service: Cache service for the repository.
            session: Optional SQLAlchemy session to be used.
        """
        self.cache_service = cache_service
        self._session = session

    @property
    def session(self) -> Session:
        """
        Get the SQLAlchemy session for the repository.

        Returns:
            SQLAlchemy session.
        """
        if self._session is None:
            # Get or create the session from a context variable (thread local variable)
            return db.session
        # Get the user-defined session
        return self._session

    def save(
        self,
        metadata: Study,
        update_modification_date: bool = False,
    ) -> Study:
        if update_modification_date:
            metadata.updated_at = datetime.datetime.utcnow()

        session = self.session
        metadata.groups = [session.merge(g) for g in metadata.groups]
        if metadata.owner:
            metadata.owner = session.merge(metadata.owner)
        session.add(metadata)
        session.commit()

        return metadata

    def refresh(self, metadata: Study) -> None:
        self.session.refresh(metadata)

    def get(self, study_id: str) -> Optional[Study]:
        """Get the study by ID or return `None` if not found in database."""
        # When we fetch a study, we also need to fetch the associated owner and groups
        # to check the permissions of the current user efficiently.
        return (
            self.session.execute(
                select(Study)
                .options(joinedload(Study.owner))
                .options(joinedload(Study.groups))
                .options(joinedload(Study.tags))
                .where(Study.id == study_id)
            )
            .unique()
            .scalar_one_or_none()
        )

    def one(self, study_id: str) -> Study:
        """Get the study by ID or raise `sqlalchemy.exc.NoResultFound` if not found in database."""

        # When we fetch a study, we also need to fetch the associated owner and groups
        # to check the permissions of the current user efficiently.
        stmt = (
            select(Study)
            .options(joinedload(Study.owner))
            .options(joinedload(Study.groups))
            .options(joinedload(Study.tags))
            .where(Study.id == study_id)
        )
        result = self.session.scalar(stmt.execution_options(unique=True))
        if result is None:
            raise NoResultFound(f"Study with ID {study_id} not found")
        return result

    def get_additional_data(self, study_id: str) -> Optional[StudyAdditionalData]:
        return self.session.get(StudyAdditionalData, study_id)

    def get_all(
        self,
        study_filter: StudyFilter = StudyFilter(),
        sort_by: Optional[StudySortBy] = None,
        pagination: StudyPagination = StudyPagination(),
    ) -> Sequence[Study]:
        """
        Retrieve studies based on specified filters, sorting, and pagination.

        Args:
            study_filter: composed of all filtering criteria.
            sort_by: how the user would like the results to be sorted.
            pagination: specifies the number of results to displayed in each page and the actually displayed page.

        Returns:
            The matching studies in proper order and pagination.
        """
        # When we fetch a study, we also need to fetch the associated owner and groups
        # to check the permissions of the current user efficiently.
        # We also need to fetch the additional data to display the study information
        # efficiently (see: `AbstractStorageService.get_study_information`)
        entity = with_polymorphic(Study, "*")

        q = self._search_studies(study_filter)

        # sorting
        if sort_by:
            if sort_by == StudySortBy.DATE_DESC:
                q = q.order_by(entity.created_at.desc())
            elif sort_by == StudySortBy.DATE_ASC:
                q = q.order_by(entity.created_at.asc())
            elif sort_by == StudySortBy.NAME_DESC:
                q = q.order_by(func.upper(entity.name).desc())
            elif sort_by == StudySortBy.NAME_ASC:
                q = q.order_by(func.upper(entity.name).asc())
            else:
                raise NotImplementedError(sort_by)

        # pagination
        if pagination.page_nb or pagination.page_size:
            limit = pagination.page_size
            offset = pagination.page_nb * pagination.page_size
            end = offset + limit
            if sort_by is None:
                q = q.order_by(entity.name.asc())
            if study_filter.groups or study_filter.tags:
                studies: Sequence[Study] = list(q.all())[offset:end]
                return studies
            q = q.offset(offset).limit(limit)

        studies = list(q.all())
        return studies

    def count_studies(self, study_filter: StudyFilter = StudyFilter()) -> int:
        """
        Count all studies matching with specified filters.

        Args:
            study_filter: composed of all filtering criteria.

        Returns:
            Integer, corresponding to total number of studies matching with specified filters.
        """
        q = self._search_studies(study_filter)
        return q.count()

    def _search_studies(
        self,
        study_filter: StudyFilter,
    ) -> Query[Study]:
        """
        Build a `SQL Query` based on specified filters.

        Args:
            study_filter: composed of all filtering criteria.

        Returns:
            The `Query` corresponding to specified criteria (except for permissions).
        """
        # When we fetch a study, we also need to fetch the associated owner and groups
        # to check the permissions of the current user efficiently.
        # We also need to fetch the additional data to display the study information
        # efficiently (see: `AbstractStorageService.get_study_information`)
        entity = with_polymorphic(Study, "*")

        escape_char = "\\"

        q: Query[Study] = self.session.query(entity)

        if study_filter.exists is not None:
            if study_filter.exists:
                q = q.filter(RawStudy.missing.is_(None))
            else:
                q = q.filter(not_(RawStudy.missing.is_(None)))

        q = q.options(joinedload(entity.owner))
        q = q.options(joinedload(entity.groups))
        q = q.options(joinedload(entity.tags))
        q = q.options(joinedload(entity.additional_data))

        if study_filter.managed is not None:
            if study_filter.managed:
                q = q.filter(or_(entity.type == "variantstudy", RawStudy.workspace == DEFAULT_WORKSPACE_NAME))
            else:
                q = q.filter(entity.type == "rawstudy")
                q = q.filter(RawStudy.workspace != DEFAULT_WORKSPACE_NAME)
        if study_filter.study_ids:
            q = q.filter(entity.id.in_(study_filter.study_ids)) if study_filter.study_ids else q
        if study_filter.users:
            q = q.filter(entity.owner_id.in_(study_filter.users))
        if study_filter.tags:
            upper_tags = [tag.upper() for tag in study_filter.tags]
            q = q.join(entity.tags).filter(func.upper(Tag.label).in_(upper_tags))
        if study_filter.archived is not None:
            q = q.filter(entity.archived == study_filter.archived)
        if study_filter.name:
            regex = f"%{escape_like(study_filter.name, escape_char)}%"
            q = q.filter(entity.name.ilike(regex, escape=escape_char))
        if study_filter.folder:
            regex = f"{escape_like(study_filter.folder, escape_char)}%"
            q = q.filter(entity.folder.ilike(regex, escape=escape_char))
        if study_filter.directory_id:
            q = q.filter(entity.directory_id == study_filter.directory_id)
        if study_filter.workspace:
            q = q.filter(RawStudy.workspace == study_filter.workspace)
        if study_filter.variant is not None:
            if study_filter.variant:
                q = q.filter(entity.type == "variantstudy")
            else:
                q = q.filter(entity.type == "rawstudy")
        if study_filter.versions:
            q = q.filter(entity.version.in_(study_filter.versions))

        # permissions + groups filtering
        if not study_filter.access_permissions.is_admin and study_filter.access_permissions.user_id is not None:
            condition_1 = entity.public_mode != PublicMode.NONE
            condition_2 = entity.owner_id == study_filter.access_permissions.user_id
            q1 = q.join(entity.groups).filter(Group.id.in_(study_filter.access_permissions.user_groups))
            if study_filter.groups:
                q2 = q.join(entity.groups).filter(Group.id.in_(study_filter.groups))
                q2 = q1.intersect(q2)
                q = q2.union(
                    q.join(entity.groups).filter(and_(or_(condition_1, condition_2), Group.id.in_(study_filter.groups)))
                )
            else:
                q = q1.union(q.filter(or_(condition_1, condition_2)))
        elif not study_filter.access_permissions.is_admin and study_filter.access_permissions.user_id is None:
            # return empty result
            # noinspection PyTypeChecker
            q = self.session.query(entity).filter(sql.false())
        elif study_filter.groups:
            q = q.join(entity.groups).filter(Group.id.in_(study_filter.groups))

        return q

    def get_all_raw(self, exists: Optional[bool] = None) -> Sequence[RawStudy]:
        stmt = select(RawStudy)
        if exists is not None:
            if exists:
                stmt = stmt.where(RawStudy.missing.is_(None))
            else:
                stmt = stmt.where(not_(RawStudy.missing.is_(None)))
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def delete(self, id_: str, *ids: str) -> None:
        ids = (id_,) + ids
        session = self.session
        stmt = delete(Study).where(Study.id.in_(ids))
        session.execute(stmt)
        session.commit()

    def update_tags(self, study: Study, new_tags: Sequence[str]) -> None:
        """
        Updates the tags associated with a given study in the database,
        replacing existing tags with new ones (case-insensitive).

        Args:
            study: The pre-existing study to be updated with the new tags.
            new_tags: The new tags to be associated with the input study in the database.
        """
        new_upper_tags = {tag.upper(): tag for tag in new_tags}
        session = self.session

        stmt = select(Tag).where(func.upper(Tag.label).in_(new_upper_tags))
        existing_tags = list(session.execute(stmt).scalars().all())

        for tag in existing_tags:
            if tag.label.upper() in new_upper_tags:
                new_upper_tags.pop(tag.label.upper())

        study.tags = [Tag(label=tag) for tag in new_upper_tags.values()] + existing_tags
        session.merge(study)
        session.commit()

        # Delete any tag that is not associated with any study.
        # Note: If tags are to be associated with objects other than Study, this code must be updated.
        delete_stmt = delete(Tag).where(~Tag.studies.any())
        session.execute(delete_stmt)
        session.commit()

    def list_duplicates(self) -> List[Tuple[str, str]]:
        """
        Get list of duplicates as tuples (id, path).
        """
        session = self.session
        subquery = select(Study.path).group_by(Study.path).having(func.count() > 1)
        stmt = select(Study.id, Study.path).where(Study.path.in_(subquery))
        result = session.execute(stmt)
        return cast(List[Tuple[str, str]], result.all())

    def has_children(self, uuid: str) -> bool:
        """
        Check if a study has children.

        Args:
            uuid: The `uuid` of the study to check.

        Returns:
            True if the study has children, False otherwise.
        """

        stmt = select(exists(select(Study).where(Study.parent_id == uuid)))
        result = self.session.scalar(stmt)
        return bool(result) if result is not None else False


class DirectoryRepository:
    """
    Database repository to manage Directory entities with permission checks.
    """

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize the repository.

        Args:
            session: Optional SQLAlchemy session to be used.
        """
        self._session = session

    @property
    def session(self) -> Session:
        """
        Get the SQLAlchemy session for the repository.

        Returns:
            SQLAlchemy session.
        """
        if self._session is None:
            # Get or create the session from a context variable (thread local variable)
            return db.session
        # Get the user-defined session
        return self._session

    def save(self, directory: Directory) -> Directory:
        """
        Save or update a directory in the database.

        Args:
            directory: The directory to save.

        Returns:
            The saved directory.
        """
        session = self.session
        directory.groups = [session.merge(g) for g in directory.groups]
        if directory.owner:
            directory.owner = session.merge(directory.owner)
        session.add(directory)
        session.commit()
        session.refresh(directory)
        return directory

    def get(self, directory_id: str) -> Optional[Directory]:
        """
        Get a directory by ID.

        Args:
            directory_id: The directory ID.

        Returns:
            The directory or None if not found.
        """
        return (
            self.session.execute(
                select(Directory)
                .options(joinedload(Directory.owner))
                .options(joinedload(Directory.groups))
                .options(joinedload(Directory.parent))
                .where(Directory.id == directory_id)
            )
            .unique()
            .scalar_one_or_none()
        )

    def one(self, directory_id: str) -> Directory:
        """
        Get a directory by ID or raise an exception.

        Args:
            directory_id: The directory ID.

        Returns:
            The directory.

        Raises:
            NoResultFound: If the directory is not found.
        """
        stmt = (
            select(Directory)
            .options(joinedload(Directory.owner))
            .options(joinedload(Directory.groups))
            .options(joinedload(Directory.parent))
            .where(Directory.id == directory_id)
        )
        result = self.session.scalar(stmt.execution_options(unique=True))
        if result is None:
            raise NoResultFound(f"Directory with ID {directory_id} not found")
        return result

    def get_all(self, access_permissions: AccessPermissions = AccessPermissions()) -> Sequence[Directory]:
        """
        Get all directories the user has access to.

        Args:
            access_permissions: User permissions for filtering.

        Returns:
            List of directories the user can access.
        """
        stmt = (
            select(Directory)
            .options(joinedload(Directory.owner))
            .options(joinedload(Directory.groups))
            .options(joinedload(Directory.parent))
        )

        # Apply permission filtering
        if not access_permissions.is_admin and access_permissions.user_id is not None:
            # User can see directories they own OR directories shared with their groups
            stmt = stmt.where(
                or_(
                    Directory.owner_id == access_permissions.user_id,
                    Directory.groups.any(Group.id.in_(access_permissions.user_groups)),
                )
            )
        elif not access_permissions.is_admin and access_permissions.user_id is None:
            # No user, return empty result
            stmt = stmt.where(sql.false())

        result = self.session.execute(stmt)
        return list(result.unique().scalars().all())

    def delete(self, directory_id: str) -> None:
        """
        Delete a directory.

        Args:
            directory_id: The directory ID to delete.
        """
        session = self.session
        stmt = delete(Directory).where(Directory.id == directory_id)
        session.execute(stmt)
        session.commit()

    def get_children(self, directory_id: str, access_permissions: AccessPermissions = AccessPermissions()) -> Sequence[Directory]:
        """
        Get all direct child directories of a parent directory.

        Args:
            directory_id: The parent directory ID.
            access_permissions: User permissions for filtering.

        Returns:
            List of child directories the user can access.
        """
        stmt = (
            select(Directory)
            .options(joinedload(Directory.owner))
            .options(joinedload(Directory.groups))
            .options(joinedload(Directory.parent))
            .where(Directory.parent_id == directory_id)
        )

        # Apply permission filtering
        if not access_permissions.is_admin and access_permissions.user_id is not None:
            # User can see directories they own OR directories shared with their groups
            stmt = stmt.where(
                or_(
                    Directory.owner_id == access_permissions.user_id,
                    Directory.groups.any(Group.id.in_(access_permissions.user_groups)),
                )
            )
        elif not access_permissions.is_admin and access_permissions.user_id is None:
            # No user, return empty result
            stmt = stmt.where(sql.false())

        result = self.session.execute(stmt)
        return list(result.unique().scalars().all())

    def has_children_directories(self, directory_id: str) -> bool:
        """
        Check if a directory has child directories.

        Args:
            directory_id: The directory ID.

        Returns:
            True if the directory has children, False otherwise.
        """
        stmt = select(exists(select(Directory).where(Directory.parent_id == directory_id)))
        result = self.session.scalar(stmt)
        return bool(result) if result is not None else False

    def has_studies(self, directory_id: str) -> bool:
        """
        Check if a directory contains studies.

        Args:
            directory_id: The directory ID.

        Returns:
            True if the directory contains studies, False otherwise.
        """
        stmt = select(exists(select(Study).where(Study.directory_id == directory_id)))
        result = self.session.scalar(stmt)
        return bool(result) if result is not None else False

    def count_studies(self, directory_id: str) -> int:
        """
        Count the number of studies in a directory.

        Args:
            directory_id: The directory ID.

        Returns:
            Number of studies in the directory.
        """
        stmt = select(func.count(Study.id)).where(Study.directory_id == directory_id)
        result = self.session.scalar(stmt)
        return int(result) if result is not None else 0

    def has_permission(
        self, directory: Directory, access_permissions: AccessPermissions, write_access: bool = False
    ) -> bool:
        """
        Check if the user has permission to access a directory.

        Permissions are granted if:
        - User is admin
        - User is the owner
        - User belongs to one of the directory's groups

        Args:
            directory: The directory to check.
            access_permissions: User permissions.
            write_access: If True, check write permissions (currently same as read).

        Returns:
            True if the user has permission, False otherwise.
        """
        if access_permissions.is_admin:
            return True

        if access_permissions.user_id is None:
            return False

        # Check if user is owner
        if directory.owner_id == access_permissions.user_id:
            return True

        # Check if user belongs to one of the directory's groups
        directory_group_ids = {g.id for g in directory.groups}
        if any(group_id in directory_group_ids for group_id in access_permissions.user_groups):
            return True

        return False

    def check_cycle(self, directory_id: str, new_parent_id: Optional[str]) -> bool:
        """
        Check if moving a directory to a new parent would create a cycle.

        Args:
            directory_id: The directory to move.
            new_parent_id: The new parent directory ID.

        Returns:
            True if a cycle would be created, False otherwise.
        """
        if new_parent_id is None:
            return False

        if directory_id == new_parent_id:
            return True

        # Traverse up the parent chain to detect cycles
        current_id = new_parent_id
        visited = {directory_id}

        while current_id is not None:
            if current_id in visited:
                return True  # Cycle detected
            visited.add(current_id)

            # Get the parent of the current directory
            stmt = select(Directory.parent_id).where(Directory.id == current_id)
            current_id = self.session.scalar(stmt)

        return False

    def has_duplicate_name(self, name: str, parent_id: Optional[str], exclude_id: Optional[str] = None) -> bool:
        """
        Check if a directory with the same name already exists under the same parent.

        Args:
            name: The directory name to check.
            parent_id: The parent directory ID.
            exclude_id: Optional directory ID to exclude from the check (for updates).

        Returns:
            True if a duplicate exists, False otherwise.
        """
        stmt = select(exists(select(Directory).where(Directory.name == name, Directory.parent_id == parent_id)))

        if exclude_id:
            stmt = select(
                exists(
                    select(Directory).where(
                        Directory.name == name, Directory.parent_id == parent_id, Directory.id != exclude_id
                    )
                )
            )

        result = self.session.scalar(stmt)
        return bool(result) if result is not None else False
