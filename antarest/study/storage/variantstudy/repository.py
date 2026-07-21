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

from antarest.core.exceptions import StudyNotFoundError
from antarest.core.interfaces.cache import ICache
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.sql_utils import upsert_multiple
from antarest.dbmodel import get_row_representation_as_dict
from antarest.study.model import RawStudy, Study
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.variantstudy.model.dbmodel import (
    CommandBlock,
    CommandBlocksWithVersion,
    CommandsListVersion,
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

    def get_study_with_commands(self, variant_id: str) -> VariantStudy | None:
        """
        Use a single JOIN query to retrieve a variant study with its associated command blocks.
        It returns a `VariantStudy` object with its associated `owner`, `groups` to be able to check user permissions efficiently.
        """
        stmt = (
            select(VariantStudy)
            .options(joinedload(VariantStudy.owner), joinedload(VariantStudy.groups), joinedload(VariantStudy.commands))
            .where(VariantStudy.id == variant_id)
        )

        result: VariantStudy | None = self.session.execute(stmt).unique().scalar_one_or_none()
        return result

    def get_command_blocks_with_associated_version(
        self, variant_ids: Sequence[str], with_lock: bool = False
    ) -> CommandBlocksWithVersion:
        """
        This method performs a single JOIN query to ensure that the 2 separated infos (version and cmd blocks) are synchronized.
        The `version` corresponds to the last given id as it's the child of the other ids.
        """
        last_child = variant_ids[-1]

        query = (
            select(CommandsListVersion, CommandBlock)
            .outerjoin(CommandBlock, CommandBlock.study_id == CommandsListVersion.variant_id)
            .where(CommandsListVersion.variant_id.in_(variant_ids))
        )

        if with_lock:
            query = query.with_for_update()

        rows = self.session.execute(query).all()

        cmd_blocks = []
        for row in rows:
            row_as_dict = get_row_representation_as_dict(row)
            command_block = row_as_dict["CommandBlock"]
            if command_block is not None:
                cmd_blocks.append(command_block)
            commands_version = row_as_dict["CommandsListVersion"]
            if commands_version.variant_id == last_child:
                version = commands_version.version

        # Sort the commands by their variant id and their index to apply them in the right order.
        sorted_cmds = sorted(cmd_blocks, key=lambda cb: (variant_ids.index(cb.study_id), cb.index))

        return CommandBlocksWithVersion(version=version, commands=sorted_cmds)

    def get_commands_list_version(self, variant_id: str) -> int:
        """
        This method should only be used to increment the commands' list version later.
        That is why it locks the `CommandsListVersion` table using a `with_for_update` clause.
        """
        stmt = select(CommandsListVersion.version).where(CommandsListVersion.variant_id == variant_id).with_for_update()
        version: int = self.session.execute(stmt).scalar_one()
        return version

    def save_commands_list_version(self, variant_id: str, commands: CommandBlocksWithVersion) -> None:
        session = self.session
        # Clean commands
        session.execute(delete(CommandBlock).where(CommandBlock.study_id == variant_id))
        # Save the new ones
        if commands.commands:
            values = [command.to_dict() for command in commands.commands]
            upsert_multiple(session, CommandBlock.__table__, values)  # type: ignore
        # Save the new command version
        self._save_commands_list_version(variant_id, commands.version)  # This performs the `commit`

    def initialize_commands_list_version_table(self, variant_id: str) -> None:
        self._save_commands_list_version(variant_id, 0)

    def _save_commands_list_version(self, variant_id: str, version: int) -> None:
        data = CommandsListVersion(variant_id=variant_id, version=version)
        session = self.session
        data = session.merge(data)
        session.add(data)
        session.commit()

    def increment_commands_list_version(self, variant_id: str) -> None:
        current_version = self.get_commands_list_version(variant_id)
        self._save_commands_list_version(variant_id, current_version + 1)

    def is_snapshot_up_to_date(self, study_id: str) -> bool:
        join_query = [joinedload(VariantStudy.snapshot), joinedload(VariantStudy.commands_version)]
        variant: VariantStudy | None = self.session.get(VariantStudy, study_id, options=join_query)

        if not variant:
            raise StudyNotFoundError(study_id)

        if not variant.snapshot:
            return False

        return variant.snapshot.version == variant.commands_version.version  # type: ignore

    def get_study_tree(self, study_ids: Sequence[str]) -> tuple[RawStudy, list[VariantStudy]]:
        """
        Returns the parent study and the list of its variants based on the given ids.
        Loads metadata at the same time for permission checks.
        """
        stmt = select(Study).options(joinedload(Study.owner), joinedload(Study.groups)).where(Study.id.in_(study_ids))

        result = self.session.execute(stmt).unique().scalars().all()

        index = {id_: i for i, id_ in enumerate(study_ids)}
        result = sorted(result, key=lambda v: index[v.id])
        return result[0], result[1:]  # type: ignore
