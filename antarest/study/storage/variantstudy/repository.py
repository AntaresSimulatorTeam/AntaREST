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

from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.sql.selectable import CTE
from typing_extensions import override

from antarest.core.interfaces.cache import ICache
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.sql_utils import upsert_one
from antarest.study.model import Study
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.variantstudy.model.dbmodel import (
    COMMANDS_LIST_VERSION_TABLE,
    CommandBlock,
    CommandBlocksWithVersion,
    VariantStudy,
)


class VariantStudyRepository(StudyMetadataRepository):
    """
    Variant study repository
    """

    def __init__(self, cache_service: ICache, session: Session | None = None):
        """
        Initialize the variant study repository.

        Args:
            cache_service: Cache service for the repository.
            session: Optional SQLAlchemy session to be used.
        """
        super().__init__(cache_service)
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

    def get_ancestor_or_self_ids(self, variant_id: str) -> Sequence[str]:
        """
        Retrieve the list of ancestor variant identifiers, including the `variant_id`,
        its parent, and all predecessors of the parent, up to and including the ID
        of the root study (`RawStudy`).

        Args:
            variant_id: Unique identifier of the child variant.

        Returns:
            Ordered list of study identifiers.
        """
        cte = self._ancestor_or_self_cte(variant_id)
        result = self.session.execute(select(cte.c.id))
        return [r[0] for r in result]

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

    def get_command_blocks_with_associated_version(
        self, variant_ids: Sequence[str], with_lock: bool = False
    ) -> CommandBlocksWithVersion:
        """
        This method performs a single JOIN query to ensure that the 2 separated infos (version and cmd blocks) are synchronized.
        The `version` corresponds to the last given id as it's the child of the other ids.
        """
        last_child = variant_ids[-1]

        query = (
            select(CommandBlock, COMMANDS_LIST_VERSION_TABLE)
            .join(COMMANDS_LIST_VERSION_TABLE, CommandBlock.study_id == COMMANDS_LIST_VERSION_TABLE.c.variant_id)
            .where(COMMANDS_LIST_VERSION_TABLE.c.variant_id.in_(variant_ids))
        )

        if with_lock:
            query = query.with_for_update()

        rows = self.session.execute(query).all()

        if not rows:
            # Means that no command blocks were found for the given variant IDs
            # We still have to fetch the version for the last variant id
            version = self.get_commands_list_version(last_child)
            return CommandBlocksWithVersion(version=version, commands=[])

        cmd_blocks = []
        for row in rows:
            cmd_blocks.append(row[0])
            if row[1].variant_id == last_child:
                version = row[1].version

        # Sort the commands by their variant id and their index to apply them in the right order.
        sorted_cmds = sorted(cmd_blocks, key=lambda cb: (variant_ids.index(cb.study_id), cb.index))

        return CommandBlocksWithVersion(version=version, commands=sorted_cmds)

    def get_commands_list_version(self, variant_id: str) -> int:
        _table = COMMANDS_LIST_VERSION_TABLE
        stmt = select(_table.c.version).where(_table.c.variant_id == variant_id)
        version: int = self.session.execute(stmt).scalar_one().version
        return version

    def save_commands_list_version(self, variant_id: str, commands: CommandBlocksWithVersion) -> None:
        session = self.session
        # Clean commands
        session.execute(delete(CommandBlock).where(CommandBlock.study_id == variant_id))
        # Save the new ones
        if commands.commands:
            session.add_all(commands.commands)
        # Save the new command version
        upsert_one(session, COMMANDS_LIST_VERSION_TABLE, {"variant_id": variant_id, "version": commands.version})
        # Commit all the operations
        session.commit()

    def find_variants(self, variant_ids: Sequence[str]) -> Sequence[VariantStudy]:
        """
        Find a list of variants by IDs
        """
        if not variant_ids:
            return []

        stmt = (
            select(VariantStudy)
            .options(joinedload(VariantStudy.owner), joinedload(VariantStudy.groups))
            .where(VariantStudy.id.in_(variant_ids))
        )

        result = self.session.execute(stmt).unique().scalars().all()

        index = {id_: i for i, id_ in enumerate(variant_ids)}
        return sorted(result, key=lambda v: index[v.id])
