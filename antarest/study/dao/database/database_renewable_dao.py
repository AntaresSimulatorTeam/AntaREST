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
Database implementation of ThermalDao.
"""

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, NoReturn, Sequence

import polars as pl
from sqlalchemy import CursorResult, Select, delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.core.exceptions import RenewableClusterNotFound
from antarest.study.business.model.renewable_cluster_model import (
    RenewableCluster,
    validate_renewable_cluster_against_version,
)
from antarest.study.dao.api.renewable_dao import RenewableDao
from antarest.study.dao.database.common import get_row_representation_as_dict, validate_area_exists
from antarest.study.dao.database.models.renewable import RENEWABLE_CLUSTER_TABLE
from antarest.study.dao.database.sql_utils import upsert_multiple, upsert_one

if TYPE_CHECKING:
    from antarest.study.dao.database.database_study_dao import DatabaseStudyDao


class DatabaseRenewableDao(RenewableDao):
    """Database implementation of RenewableDao"""

    def __init__(self, study_id: str, db_session: Session) -> None:
        """
        Initialize DatabaseRenewableDao with dependencies.

        Args:
            study_id: The study ID for database queries.
            db_session: SQLAlchemy session for database operations.
        """
        self._study_id = study_id
        self._db_session = db_session

    @abstractmethod
    def get_impl(self) -> "DatabaseStudyDao":
        pass

    def _convert_db_row_to_renewable(self, row: Any) -> RenewableCluster:
        data = get_row_representation_as_dict(row)
        del data["study_id"]
        del data["area_id"]
        data["id"] = data.pop("renewable_id")
        cluster = RenewableCluster(**data)
        version = self.get_impl().get_version()
        validate_renewable_cluster_against_version(version, cluster)
        return cluster

    def _convert_renewable_cluster_to_row(self, area_id: str, cluster: RenewableCluster) -> dict[str, Any]:
        values = dict(study_id=self._study_id, area_id=area_id, **cluster.model_dump())
        values["renewable_id"] = values.pop("id")
        return values

    def _raise_the_right_exception(
        self, area_id: str, renewable_id: str, exc: IntegrityError | None = None
    ) -> NoReturn:
        # Could be because area does not exist or the renewable does not exist
        validate_area_exists(self._db_session, self._study_id, area_id)
        if exc:
            raise RenewableClusterNotFound(area_id, renewable_id) from exc
        raise RenewableClusterNotFound(area_id, renewable_id)

    @override
    def save_renewable(self, area_id: str, renewable: RenewableCluster) -> None:
        session = self._db_session

        values = self._convert_renewable_cluster_to_row(area_id, renewable)
        try:
            upsert_one(session, RENEWABLE_CLUSTER_TABLE, values)
        except IntegrityError as e:
            self._raise_the_right_exception(area_id, renewable.id, e)

        session.commit()

    @override
    def save_renewables(self, area_id: str, renewables: Sequence[RenewableCluster]) -> None:
        if not renewables:
            return

        session = self._db_session
        values = [self._convert_renewable_cluster_to_row(area_id, renewable) for renewable in renewables]

        try:
            upsert_multiple(session=session, table=RENEWABLE_CLUSTER_TABLE, values=values)
        except IntegrityError as e:
            validate_area_exists(session, self._study_id, area_id)
            # We have to find which renewable does not exist
            existing_renewable_ids = {renew.id for renew in self.get_all_renewables_for_area(area_id)}
            for renewable in renewables:
                if renewable.id not in existing_renewable_ids:
                    self._raise_the_right_exception(area_id, renewable.id, e)

        session.commit()

    @override
    def save_renewable_series(self, area_id: str, renewable_id: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def delete_renewable(self, area_id: str, renewable: RenewableCluster) -> None:
        study_id = self._study_id
        session = self._db_session
        renewable_id = renewable.id.lower()

        result = session.execute(
            delete(RENEWABLE_CLUSTER_TABLE).where(
                (RENEWABLE_CLUSTER_TABLE.c.study_id == study_id)
                & (RENEWABLE_CLUSTER_TABLE.c.area_id == area_id)
                & (RENEWABLE_CLUSTER_TABLE.c.renewable_id == renewable_id)
            )
        )
        assert isinstance(result, CursorResult)
        if result.rowcount == 0:
            # Means the DELETE had no effect so the renewable did not exist
            self._raise_the_right_exception(area_id, renewable_id)

        # TODO: depending on scenariobuilder implementation, we may need to delete some stuff from scenario builder here
        session.commit()

    @override
    def get_all_renewables(self) -> dict[str, dict[str, RenewableCluster]]:
        study_id = self._study_id
        session = self._db_session

        stmt = select(RENEWABLE_CLUSTER_TABLE).where(RENEWABLE_CLUSTER_TABLE.c.study_id == study_id)
        rows = session.execute(stmt).fetchall()

        renewables_by_areas: dict[str, dict[str, RenewableCluster]] = {}
        for row in rows:
            renewable = self._convert_db_row_to_renewable(row)
            renewables_by_areas.setdefault(row.area_id, {})[renewable.id.lower()] = renewable
        return renewables_by_areas

    @override
    def get_all_renewables_for_area(self, area_id: str) -> Sequence[RenewableCluster]:
        study_id = self._study_id
        session = self._db_session
        validate_area_exists(session, study_id, area_id)

        stmt = select(RENEWABLE_CLUSTER_TABLE).where(
            (RENEWABLE_CLUSTER_TABLE.c.study_id == study_id) & (RENEWABLE_CLUSTER_TABLE.c.area_id == area_id)
        )
        rows = session.execute(stmt).fetchall()
        return [self._convert_db_row_to_renewable(row) for row in rows]

    def _select_renewable_cluster(self, area_id: str, renewable_id: str) -> Select[Any]:
        study_id = self._study_id
        return select(RENEWABLE_CLUSTER_TABLE).where(
            (RENEWABLE_CLUSTER_TABLE.c.study_id == study_id)
            & (RENEWABLE_CLUSTER_TABLE.c.area_id == area_id)
            & (RENEWABLE_CLUSTER_TABLE.c.renewable_id == renewable_id)
        )

    @override
    def get_renewable(self, area_id: str, renewable_id: str) -> RenewableCluster:
        session = self._db_session
        stmt = self._select_renewable_cluster(area_id, renewable_id)
        row = session.execute(stmt).fetchone()
        if not row:
            self._raise_the_right_exception(area_id, renewable_id)

        return self._convert_db_row_to_renewable(row)

    @override
    def renewable_exists(self, area_id: str, renewable_id: str) -> bool:
        session = self._db_session
        stmt = self._select_renewable_cluster(area_id, renewable_id)
        return session.execute(stmt).fetchone() is not None

    @override
    def get_renewable_series(self, area_id: str, renewable_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")
