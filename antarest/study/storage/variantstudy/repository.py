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

from sqlalchemy import select
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
        top_query = select(Study.id, Study.parent_id).where(Study.id == variant_id)
        top_q = top_query.cte("study_cte", recursive=True)

        bot_q = select(Study.id, Study.parent_id).join(top_q, Study.id == top_q.c.parent_id)

        recursive_q = top_q.union_all(bot_q)
        result = self.session.execute(select(recursive_q.c.id))
        return [r[0] for r in result]

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

    def find_variants(self, variant_ids: Sequence[str]) -> Sequence[VariantStudy]:
        """
        Find a list of variants by IDs
        """
        if not variant_ids:
            return []

        stmt = (
            select(VariantStudy)
            .options(
                joinedload(VariantStudy.snapshot),
                joinedload(VariantStudy.commands),
                joinedload(VariantStudy.owner),
                joinedload(VariantStudy.groups),
            )
            .where(VariantStudy.id.in_(variant_ids))
        )

        result = self.session.execute(stmt).unique().scalars().all()

        index = {id_: i for i, id_ in enumerate(variant_ids)}
        return sorted(result, key=lambda v: index[v.id])
