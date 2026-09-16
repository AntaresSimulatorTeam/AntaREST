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

"""
Queries on the study data tables that are not scoped to a single `DatabaseStudyDao`.

The garbage collectors (matrices, blobs) walk these tables across all studies, so they
cannot go through a per-study DAO. Gathering their queries here keeps the way study data
rows are linked back to a study in one place.
"""

from collections.abc import Iterator, Sequence

from sqlalchemy import ColumnElement, Table, select
from sqlalchemy.orm import Session

from antarest.study.dao.database.models import STUDY_DATA_TABLE
from antarest.study.dao.database.models.user_resources import USER_RESOURCES_TABLE


def belongs_to_study(table: Table, study_id: str) -> ColumnElement[bool]:
    """
    Predicate restricting a study data table to the rows of the given study.

    Args:
        table: Any study data table, i.e. any table keyed by a study.
        study_id: The study ID, as found in `study.id`.

    Note:
        Study data tables are keyed by `study_data_id`, not by the study ID, hence the
        subquery. A study with no `study_data` row matches nothing, which is correct:
        its data rows were cascade-deleted along with it.
    """
    study_data_ids = select(STUDY_DATA_TABLE.c.study_data_id).where(STUDY_DATA_TABLE.c.study_id == study_id)
    return table.c.study_data_id.in_(study_data_ids)


def yield_matrix_ids(session: Session, tables: Sequence[Table], study_id: str) -> Iterator[tuple[Table, str]]:
    """
    Yield `(table, matrix_id)` for every matrix referenced by the given study.

    Used by the matrix garbage collector: a matrix missing from this listing is
    considered unused and becomes eligible for deletion.
    """
    for table in tables:
        stmt = select(table.c.matrix_id).where(belongs_to_study(table, study_id))
        for row in session.execute(stmt).fetchall():
            yield table, row.matrix_id


def yield_used_blobs(session: Session) -> Iterator[tuple[str, str]]:
    """
    Yield `(blob_id, study_id)` for every blob referenced by a user resource, across all studies.

    Used by the blob garbage collector: a blob missing from this listing is considered
    unused and becomes eligible for deletion.

    Note:
        The join back to `study_data` only recovers the study ID for the usage description.
        It cannot hide a used blob: `user_resources.study_data_id` is `NOT NULL` and carries
        a foreign key onto `study_data`, so every row has exactly one match.
    """
    stmt = (
        select(USER_RESOURCES_TABLE.c.blob_id, STUDY_DATA_TABLE.c.study_id)
        .join(STUDY_DATA_TABLE, USER_RESOURCES_TABLE.c.study_data_id == STUDY_DATA_TABLE.c.study_data_id)
        .where(USER_RESOURCES_TABLE.c.blob_id.isnot(None))
    )
    for row in session.execute(stmt).fetchall():
        yield row.blob_id, row.study_id
