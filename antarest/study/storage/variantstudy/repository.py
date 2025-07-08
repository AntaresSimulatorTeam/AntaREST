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

from typing import List, Optional, Sequence, cast

from sqlalchemy.orm import Session, joinedload
from typing_extensions import override

from antarest.core.interfaces.cache import ICache
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.study.model import Study
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.variantstudy.model.dbmodel import CommandBlock, VariantStudy


class VariantStudyRepository(StudyMetadataRepository):
    """
    Variant study repository
    """

    def __init__(self, cache_service: ICache, session: Optional[Session] = None):
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

    def get_children(self, parent_id: str) -> List[VariantStudy]:
        """
        Get the direct children of a variant study in chronological order.

        Args:
            parent_id: Identifier of the parent study.

        Returns:
            List of `VariantStudy` objects, ordered by creation date.
        """
        q = self.session.query(VariantStudy).filter(Study.parent_id == parent_id)
        q = q.order_by(Study.created_at.desc())
        studies = cast(List[VariantStudy], q.all())
        return studies

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
        # see: [Recursive Queries](https://www.postgresql.org/docs/current/queries-with.html#QUERIES-WITH-RECURSIVE)
        top_q = self.session.query(Study.id, Study.parent_id)
        top_q = top_q.filter(Study.id == variant_id)
        top_q = top_q.cte("study_cte", recursive=True)

        bot_q = self.session.query(Study.id, Study.parent_id)
        bot_q = bot_q.join(top_q, Study.id == top_q.c.parent_id)

        recursive_q = top_q.union_all(bot_q)
        q = self.session.query(recursive_q)
        return [r[0] for r in q]

    def get_all_command_blocks(self) -> List[CommandBlock]:
        """
        Get all command blocks.

        Returns:
            List of `CommandBlock` objects.
        """
        cmd_blocks: List[CommandBlock] = self.session.query(CommandBlock).all()
        return cmd_blocks

    def find_variants(self, variant_ids: Sequence[str]) -> Sequence[VariantStudy]:
        """
        Find a list of variants by IDs

        Args:
            variant_ids: list of variant IDs.

        Returns:
            List of variants (and attached snapshot) ordered by IDs
        """
        # When we fetch the list of variants, we also need to fetch the associated snapshots,
        # the list of commands, the additional data, etc.
        # We use a SQL query with joins to fetch all these data efficiently.
        q = (
            self.session.query(VariantStudy)
            .options(joinedload(VariantStudy.snapshot))
            .options(joinedload(VariantStudy.commands))
            .options(joinedload(VariantStudy.additional_data))
            .options(joinedload(VariantStudy.owner))
            .options(joinedload(VariantStudy.groups))
            .filter(VariantStudy.id.in_(variant_ids))  # type: ignore
        )
        index = {id_: i for i, id_ in enumerate(variant_ids)}
        return sorted(q, key=lambda v: index[v.id])
