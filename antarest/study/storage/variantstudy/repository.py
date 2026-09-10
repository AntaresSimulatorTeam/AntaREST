# Copyright (c) 2026, RTE (https://www.rte-france.com)
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

from typing import cast

from sqlalchemy import literal, select
from sqlalchemy.orm import Session, joinedload, with_polymorphic
from sqlalchemy.sql.selectable import CTE
from typing_extensions import override

from antarest.core.exceptions import StudyNotFoundError
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.study.model import RawStudy, Study
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.variantstudy.model.dbmodel import (
    CommandBlock,
    CommandsListVersion,
    LineageVersions,
    VariantStudy,
    VariantStudySnapshot,
)


class VariantStudyRepository(StudyMetadataRepository):
    """
    Variant study repository

    Notes:
        Important design notes for handling concurrency :
         - we want to ensure that the list of commands defining a study is not modified concurrently by multiple
           requests
         - we also want to ensure that a snapshot correctly identifies to which list of commands it corresponds

         Therefore, we use a "version" for the list of commands, which MUST be locked with a "FOR UPDATE" prior to any
         modification. The version MUST be incremented after any modification, and committed together with the new
         list of commands.
         Also, we MUST always read the version and the list of commands together in a single query (not transaction),
         so that we are sure they are consistent, even in READ COMMITTED isolation level.
    """

    def __init__(self, session: Session | None = None):
        """
        Initialize the variant study repository.

        Args:
            session: Optional SQLAlchemy session to be used.
        """
        super().__init__(session)
        self._session = session

    @override
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

    def get_children(self, parent_id: str) -> list[VariantStudy]:
        """
        Get the direct children of a variant study in chronological order.

        Args:
            parent_id: Identifier of the parent study.

        Returns:
            List of `VariantStudy` objects, ordered by creation date.
        """
        stmt = select(VariantStudy).where(Study.parent_id == parent_id).order_by(Study.created_at.desc())
        result = self.session.execute(stmt)
        studies = list(result.scalars().all())
        return studies

    def _ancestor_or_self_cte(self, variant_id: str) -> CTE:
        """
        Build a recursive CTE yielding (id, parent_id) for `variant_id` and every ancestor.
        See: https://www.postgresql.org/docs/current/queries-with.html#QUERIES-WITH-RECURSIVE
        """
        top_q = select(Study.id, Study.parent_id).where(Study.id == variant_id).cte("study_cte", recursive=True)
        bot_q = select(Study.id, Study.parent_id).join(top_q, Study.id == top_q.c.parent_id)
        return top_q.union_all(bot_q)

    def get_root_ancestor_id(self, variant_id: str) -> str | None:
        """
        Return the id of the topmost ancestor of `variant_id`, or `variant_id` itself if
        it has no parent. Returns None if `variant_id` does not exist.
        """
        cte = self._ancestor_or_self_cte(variant_id)
        return self.session.execute(select(cte.c.id).where(cte.c.parent_id.is_(None))).scalar_one_or_none()

    def get_all_descendants(self, parent_id: str) -> list[VariantStudy]:
        """
        Get all variant descendants of a study recursively.

        Args:
            parent_id: Identifier of the ancestor study.

        Returns:
            List of all variants descendants.
        """
        base_q = select(Study.id).where(Study.parent_id == parent_id)
        cte = base_q.cte("descendants_cte", recursive=True)

        recursive_q = select(Study.id).join(cte, Study.parent_id == cte.c.id)

        full_cte = cte.union_all(recursive_q)
        stmt = select(VariantStudy).where(VariantStudy.id.in_(select(full_cte.c.id)))
        return list(self.session.execute(stmt).scalars().all())

    def get_all_command_blocks(self) -> list[CommandBlock]:
        """
        Get all command blocks.

        Returns:
            List of `CommandBlock` objects.
        """
        stmt = select(CommandBlock)
        return list(self.session.execute(stmt).scalars().all())

    def get_study_with_commands(self, variant_id: str, with_lock: bool = False) -> VariantStudy:
        """
        Use a single JOIN query to retrieve a variant study with its associated command blocks and their version.
        It returns a `VariantStudy` object with its associated `owner`, `groups` to be able to check user permissions efficiently.
        """
        # postgresql does not allow to lock the version row in the main query which uses outer joins,
        # therefore we need to first lock the row with a separate query
        if with_lock:
            self.session.execute(
                select(CommandsListVersion).where(CommandsListVersion.variant_id == variant_id).with_for_update()
            )
        join_query = [
            joinedload(VariantStudy.owner),
            joinedload(VariantStudy.groups),
            joinedload(VariantStudy.commands),
            joinedload(VariantStudy.commands_version),
        ]
        stmt = select(VariantStudy).options(*join_query).where(VariantStudy.id == variant_id)

        variant_study: VariantStudy | None = self.session.execute(stmt).unique().scalar_one_or_none()

        if not variant_study:
            raise StudyNotFoundError(variant_id)

        return variant_study

    def get_commands_list_version(self, variant_id: str) -> int:
        """
        This method should only be used to increment the commands' list version later.
        That is why it locks the `CommandsListVersion` table using a `with_for_update` clause.
        """
        stmt = select(CommandsListVersion.version).where(CommandsListVersion.variant_id == variant_id).with_for_update()
        version: int = self.session.execute(stmt).scalar_one()
        return version

    def increment_commands_list_version(self, variant_id: str) -> None:
        """
        Locks and increments the commands' list version of that variant.

        The lock is necessary to ensure no other operation increments the value at the same time
        (new command addition, ...).
        """
        current_version = self.get_commands_list_version(variant_id)
        data = CommandsListVersion(variant_id=variant_id, version=current_version + 1)
        session = self.session
        data = session.merge(data)
        session.add(data)
        session.commit()

    def get_study_lineage(self, variant_id: str) -> tuple[RawStudy, list[VariantStudy]]:
        """
        Returns the lineage of parents of the study, including the study itself.

        The root study is returned first, then the ordered list of its children, until and including
        the specified variant.
        Also loads metadata, commands and snapshot at the same time to avoid multiple queries.
        """
        base_q = select(Study.id, Study.parent_id, literal(0).label("depth")).where(Study.id == variant_id)
        cte = base_q.cte("ancestor_cte", recursive=True)
        recursive_q = select(Study.id, Study.parent_id, (cte.c.depth + 1).label("depth")).join(
            cte, Study.id == cte.c.parent_id
        )
        cte = cte.union_all(recursive_q)

        study_w_p = with_polymorphic(Study, [VariantStudy])

        stmt = select(study_w_p).join(cte, study_w_p.id == cte.c.id).order_by(cte.c.depth.desc())
        # TODO: the joinedload of groups and owner should not be necessary here, but repository.save(study)
        #       will fetch groups anyway. Maybe something we want to change.
        stmt = stmt.options(
            joinedload(study_w_p.owner),
            joinedload(study_w_p.groups),
            joinedload(study_w_p.VariantStudy.snapshot),
            joinedload(study_w_p.VariantStudy.commands),
            joinedload(study_w_p.VariantStudy.commands_version),
        )
        lineage = list(self.session.execute(stmt).unique().scalars().all())
        if not lineage:
            raise StudyNotFoundError(variant_id)
        return cast(RawStudy, lineage[0]), [cast(VariantStudy, v) for v in lineage[1:]]

    def get_refreshed_snapshot(self, variant_id: str) -> VariantStudySnapshot | None:
        return self.session.execute(
            select(VariantStudySnapshot)
            .where(VariantStudySnapshot.id == variant_id)
            .execution_options(populate_existing=True)
        ).scalar_one_or_none()

    def is_snapshot_up_to_date(self, variant_id: str) -> bool:
        snapshot_versions = self.session.execute(
            select(VariantStudySnapshot.lineage_versions).where(VariantStudySnapshot.id == variant_id)
        ).scalar_one_or_none()
        if snapshot_versions is None:
            return False
        current_versions = self.get_lineage_versions(variant_id)
        return snapshot_versions.is_up_to_date_with(current_versions)

    def get_lineage_versions(self, variant_id: str) -> LineageVersions:
        base_q = select(Study.id, Study.parent_id, literal(0).label("depth")).where(Study.id == variant_id)
        cte = base_q.cte("ancestor_cte", recursive=True)
        recursive_q = select(Study.id, Study.parent_id, (cte.c.depth + 1).label("depth")).join(
            cte, Study.id == cte.c.parent_id
        )
        cte = cte.union_all(recursive_q)

        study_w_p = with_polymorphic(Study, [VariantStudy])

        stmt = (
            select(study_w_p.id, CommandsListVersion.version)
            .join(study_w_p.VariantStudy.commands_version)
            .join(cte, study_w_p.id == cte.c.id)
            .order_by(cte.c.depth.desc())
        )
        lineage_data = self.session.execute(stmt).all()

        return LineageVersions([(row[0], row[1]) for row in lineage_data])
