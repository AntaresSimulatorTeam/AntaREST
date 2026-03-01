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
Database implementation of XpansionDao.
"""

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Optional

import polars as pl
from pydantic import TypeAdapter
from sqlalchemy import CursorResult, delete, insert, select
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.core.exceptions import (
    AreaNotFound,
    CandidateNotFoundError,
    LinkNotFound,
    XpansionCandidateDeletionError,
    XpansionConfigurationAlreadyExists,
    XpansionConfigurationDoesNotExist,
)
from antarest.core.serde.json import from_json, to_json_string
from antarest.study.business.model.xpansion_model import (
    XpansionAdequacyCriterion,
    XpansionAdequacyPattern,
    XpansionCandidate,
    XpansionResourceFileType,
    XpansionSensitivitySettings,
    XpansionSettings,
    XpansionSettingsUpdate,
)
from antarest.study.dao.api.xpansion_dao import XpansionDao
from antarest.study.dao.database.common import get_row_representation_as_dict
from antarest.study.dao.database.models.xpansion import (
    XPANSION_ADEQUACY_CRITERION_TABLE,
    XPANSION_CANDIDATE_TABLE,
    XPANSION_SETTINGS_TABLE,
)
from antarest.study.dao.database.sql_utils import upsert_one

if TYPE_CHECKING:
    from antarest.study.dao.database.database_study_dao import DatabaseStudyDao

_ADEQUACY_PATTERNS_ADAPTER: TypeAdapter[list[XpansionAdequacyPattern]] = TypeAdapter(list[XpansionAdequacyPattern])
_PROJECTION_ADAPTER: TypeAdapter[list[str]] = TypeAdapter(list[str])


class DatabaseXpansionDao(XpansionDao):
    """Database implementation of XpansionDao."""

    def __init__(self, study_id: str, db_session: Session) -> None:
        self._study_id = study_id
        self._db_session = db_session

    @abstractmethod
    def get_impl(self) -> "DatabaseStudyDao":
        pass

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _settings_row_exists(self) -> bool:
        stmt = select(XPANSION_SETTINGS_TABLE.c.study_id).where(XPANSION_SETTINGS_TABLE.c.study_id == self._study_id)
        return self._db_session.execute(stmt).fetchone() is not None

    def _candidate_to_row(self, candidate: XpansionCandidate) -> dict[str, Any]:
        data = candidate.model_dump()
        data.pop("link")
        return {
            "study_id": self._study_id,
            "link_area_from": candidate.link.area_from,
            "link_area_to": candidate.link.area_to,
            **data,
        }

    def _row_to_candidate(self, row: Any) -> XpansionCandidate:
        data = get_row_representation_as_dict(row)
        area_from = data.pop("link_area_from")
        area_to = data.pop("link_area_to")
        del data["study_id"]
        # Pass the link as a string so the XpansionLinkStr validator parses it.
        data["link"] = f"{area_from} - {area_to}"
        return XpansionCandidate(**data)

    def _assert_link_exists(self, candidate: XpansionCandidate) -> None:
        area_from = candidate.link.area_from
        area_to = candidate.link.area_to

        invalid = self.get_impl().get_invalid_area_ids([area_from, area_to])
        if invalid:
            raise AreaNotFound(*invalid)

        if not self.get_impl().link_exists(area_from, area_to):
            raise LinkNotFound(f"The link from '{area_from}' to '{area_to}' not found")

    # ------------------------------------------------------------------
    # XpansionDao — configuration lifecycle
    # ------------------------------------------------------------------

    @override
    def create_xpansion_configuration(self) -> None:
        if self._settings_row_exists():
            raise XpansionConfigurationAlreadyExists(self._study_id)

        self.save_xpansion_settings(XpansionSettings())
        self.save_xpansion_adequacy_criterion(XpansionAdequacyCriterion())

    @override
    def delete_xpansion_configuration(self) -> None:
        result = self._db_session.execute(
            delete(XPANSION_SETTINGS_TABLE).where(XPANSION_SETTINGS_TABLE.c.study_id == self._study_id)
        )
        assert isinstance(result, CursorResult)
        if result.rowcount == 0:
            raise XpansionConfigurationDoesNotExist(self._study_id)
        # Cascade on xpansion_candidate and xpansion_adequacy_criterion handles the rest.
        self._db_session.commit()

    # ------------------------------------------------------------------
    # XpansionDao — settings
    # ------------------------------------------------------------------

    @override
    def get_xpansion_settings(self) -> XpansionSettings:
        stmt = select(XPANSION_SETTINGS_TABLE).where(XPANSION_SETTINGS_TABLE.c.study_id == self._study_id)
        row = self._db_session.execute(stmt).fetchone()
        if not row:
            raise XpansionConfigurationDoesNotExist(self._study_id)

        data = get_row_representation_as_dict(row)
        del data["study_id"]

        sensitivity_config = XpansionSensitivitySettings(
            epsilon=data.pop("sensitivity_epsilon"),
            capex=data.pop("sensitivity_capex"),
            projection=from_json(data.pop("sensitivity_projection")),
        )
        # Nullable columns: map NULL back to the empty-string default.
        data["yearly_weights"] = data.get("yearly_weights") or ""
        data["additional_constraints"] = data.get("additional_constraints") or ""

        return XpansionSettings(sensitivity_config=sensitivity_config, **data)

    @override
    def save_xpansion_settings(self, settings: XpansionSettings) -> None:
        sensitivity = settings.sensitivity_config
        values: dict[str, Any] = {
            "study_id": self._study_id,
            "master": settings.master,
            "uc_type": settings.uc_type,
            "optimality_gap": settings.optimality_gap,
            "relative_gap": settings.relative_gap,
            "relaxed_optimality_gap": settings.relaxed_optimality_gap,
            "max_iteration": settings.max_iteration,
            "solver": settings.solver,
            "log_level": settings.log_level,
            "separation_parameter": settings.separation_parameter,
            "batch_size": settings.batch_size,
            # Store empty strings as NULL so the nullable column is consistent.
            "yearly_weights": settings.yearly_weights or None,
            "additional_constraints": settings.additional_constraints or None,
            "timelimit": settings.timelimit,
            "master_solution_tolerance": settings.master_solution_tolerance,
            "cut_coefficient_tolerance": settings.cut_coefficient_tolerance,
            "sensitivity_epsilon": sensitivity.epsilon,
            "sensitivity_capex": sensitivity.capex,
            "sensitivity_projection": to_json_string(sensitivity.projection),
        }
        upsert_one(self._db_session, XPANSION_SETTINGS_TABLE, values)
        self._db_session.commit()

    @override
    def checks_xpansion_settings_are_correct(self, settings: XpansionSettingsUpdate) -> None:
        # File existence checks for additional_constraints and yearly_weights
        # require blob storage access, which is not yet available in the database DAO.
        # Pydantic validation of the settings object still applies upstream.
        if settings.sensitivity_config and settings.sensitivity_config.projection is not None:
            existing_names = {c.name for c in self.get_all_xpansion_candidates()}
            invalid = [name for name in settings.sensitivity_config.projection if name not in existing_names]
            if invalid:
                raise CandidateNotFoundError(f"Candidates not found in projection: {', '.join(invalid)}")

    # ------------------------------------------------------------------
    # XpansionDao — candidates
    # ------------------------------------------------------------------

    @override
    def get_all_xpansion_candidates(self) -> list[XpansionCandidate]:
        stmt = select(XPANSION_CANDIDATE_TABLE).where(XPANSION_CANDIDATE_TABLE.c.study_id == self._study_id)
        rows = self._db_session.execute(stmt).fetchall()
        return [self._row_to_candidate(row) for row in rows]

    @override
    def get_xpansion_candidate(self, candidate_id: str) -> XpansionCandidate:
        stmt = select(XPANSION_CANDIDATE_TABLE).where(
            (XPANSION_CANDIDATE_TABLE.c.study_id == self._study_id) & (XPANSION_CANDIDATE_TABLE.c.name == candidate_id)
        )
        row = self._db_session.execute(stmt).fetchone()
        if not row:
            raise CandidateNotFoundError(f"The candidate '{candidate_id}' does not exist")
        return self._row_to_candidate(row)

    @override
    def save_xpansion_candidate(self, candidate: XpansionCandidate, old_id: Optional[str] = None) -> None:
        values = self._candidate_to_row(candidate)
        if old_id and old_id != candidate.name:
            # Rename: the PK changes, so delete the old row and insert a new one.
            self._db_session.execute(
                delete(XPANSION_CANDIDATE_TABLE).where(
                    (XPANSION_CANDIDATE_TABLE.c.study_id == self._study_id)
                    & (XPANSION_CANDIDATE_TABLE.c.name == old_id)
                )
            )
            self._db_session.execute(insert(XPANSION_CANDIDATE_TABLE).values(values))
        else:
            upsert_one(self._db_session, XPANSION_CANDIDATE_TABLE, values)
        self._db_session.commit()

    @override
    def delete_xpansion_candidate(self, candidate_name: str) -> None:
        result = self._db_session.execute(
            delete(XPANSION_CANDIDATE_TABLE).where(
                (XPANSION_CANDIDATE_TABLE.c.study_id == self._study_id)
                & (XPANSION_CANDIDATE_TABLE.c.name == candidate_name)
            )
        )
        assert isinstance(result, CursorResult)
        if result.rowcount == 0:
            raise CandidateNotFoundError(f"The candidate '{candidate_name}' does not exist")
        self._db_session.commit()

    @override
    def checks_xpansion_candidate_coherence(self, candidate: XpansionCandidate) -> None:
        self._assert_link_exists(candidate)
        # Link-profile file validation requires blob storage access.
        # Not yet implemented for database storage mode.

    @override
    def checks_xpansion_candidate_can_be_deleted(self, candidate_name: str) -> None:
        stmt = select(XPANSION_SETTINGS_TABLE.c.sensitivity_projection).where(
            XPANSION_SETTINGS_TABLE.c.study_id == self._study_id
        )
        row = self._db_session.execute(stmt).fetchone()
        if row:
            projection = _PROJECTION_ADAPTER.validate_json(row.sensitivity_projection)
            if candidate_name in projection:
                raise XpansionCandidateDeletionError(self._study_id, candidate_name)

    # ------------------------------------------------------------------
    # XpansionDao — adequacy criterion
    # ------------------------------------------------------------------

    @override
    def get_xpansion_adequacy_criterion(self) -> XpansionAdequacyCriterion:
        stmt = select(XPANSION_ADEQUACY_CRITERION_TABLE).where(
            XPANSION_ADEQUACY_CRITERION_TABLE.c.study_id == self._study_id
        )
        row = self._db_session.execute(stmt).fetchone()
        if not row:
            return XpansionAdequacyCriterion()

        patterns = _ADEQUACY_PATTERNS_ADAPTER.validate_json(row.patterns)
        return XpansionAdequacyCriterion(
            stopping_threshold=row.stopping_threshold,
            criterion_count_threshold=row.criterion_count_threshold,
            patterns=patterns,
        )

    @override
    def save_xpansion_adequacy_criterion(self, criterion: XpansionAdequacyCriterion) -> None:
        missing_areas = self.get_impl().get_invalid_area_ids([p.area for p in criterion.patterns])
        if missing_areas:
            raise AreaNotFound(*missing_areas)

        values: dict[str, Any] = {
            "study_id": self._study_id,
            "stopping_threshold": criterion.stopping_threshold,
            "criterion_count_threshold": criterion.criterion_count_threshold,
            "patterns": to_json_string([p.model_dump() for p in criterion.patterns]),
        }
        upsert_one(self._db_session, XPANSION_ADEQUACY_CRITERION_TABLE, values)
        self._db_session.commit()

    # ------------------------------------------------------------------
    # XpansionDao — resources (file/blob based, not yet implemented)
    # ------------------------------------------------------------------

    @override
    def get_xpansion_resource(self, resource_type: XpansionResourceFileType, filename: str) -> bytes | pl.DataFrame:
        raise NotImplementedError("Xpansion resource access requires blob storage — not yet implemented")

    @override
    def get_xpansion_resources(self, resource_type: XpansionResourceFileType) -> list[str]:
        raise NotImplementedError("Xpansion resource listing requires blob storage — not yet implemented")

    @override
    def checks_xpansion_resource_can_be_deleted(self, resource_type: XpansionResourceFileType, filename: str) -> None:
        raise NotImplementedError("Xpansion resource validation requires blob storage — not yet implemented")

    @override
    def delete_xpansion_resource(self, resource_type: XpansionResourceFileType, filename: str) -> None:
        raise NotImplementedError("Xpansion resource deletion requires blob storage — not yet implemented")

    @override
    def save_xpansion_constraint(self, filename: str, content: bytes) -> None:
        raise NotImplementedError("Xpansion resource saving requires blob storage — not yet implemented")

    @override
    def save_xpansion_capacity(self, filename: str, series: str) -> None:
        raise NotImplementedError("Xpansion resource saving requires blob storage — not yet implemented")

    @override
    def save_xpansion_weight(self, filename: str, series: str) -> None:
        raise NotImplementedError("Xpansion resource saving requires blob storage — not yet implemented")
