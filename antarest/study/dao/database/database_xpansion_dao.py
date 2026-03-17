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
from sqlalchemy import CursorResult, delete, insert, select, update
from sqlalchemy.exc import IntegrityError
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
from antarest.study.business.model.xpansion_model import (
    XpansionAdequacyCriterion,
    XpansionAdequacyPattern,
    XpansionCandidate,
    XpansionLink,
    XpansionResourceFileType,
    XpansionSensitivitySettings,
    XpansionSettings,
    XpansionSettingsUpdate,
)
from antarest.study.dao.api.xpansion_dao import XpansionDao
from antarest.study.dao.database.common import get_row_representation_as_dict
from antarest.study.dao.database.models.xpansion import (
    XPANSION_ADEQUACY_CRITERION_TABLE,
    XPANSION_ADEQUACY_PATTERN_TABLE,
    XPANSION_CANDIDATE_TABLE,
    XPANSION_SENSITIVITY_PROJECTION_TABLE,
    XPANSION_SETTINGS_TABLE,
)
from antarest.study.dao.database.sql_utils import upsert_one

if TYPE_CHECKING:
    from antarest.study.dao.database.database_study_dao import DatabaseStudyDao


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
        data["link"] = XpansionLink(area_from=area_from, area_to=area_to).serialize()
        return XpansionCandidate.model_validate(data)

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
        stmt = (
            select(XPANSION_SETTINGS_TABLE, XPANSION_SENSITIVITY_PROJECTION_TABLE.c.candidate_name)
            .outerjoin(
                XPANSION_SENSITIVITY_PROJECTION_TABLE,
                XPANSION_SETTINGS_TABLE.c.study_id == XPANSION_SENSITIVITY_PROJECTION_TABLE.c.study_id,
            )
            .where(XPANSION_SETTINGS_TABLE.c.study_id == self._study_id)
        )
        rows = self._db_session.execute(stmt).fetchall()
        if not rows:
            raise XpansionConfigurationDoesNotExist(self._study_id)

        data = get_row_representation_as_dict(rows[0])
        del data["study_id"]
        del data["candidate_name"]
        sensitivity_config = XpansionSensitivitySettings(
            epsilon=data.pop("sensitivity_epsilon"),
            capex=data.pop("sensitivity_capex"),
            projection=[r.candidate_name for r in rows if r.candidate_name is not None],
        )
        return XpansionSettings(sensitivity_config=sensitivity_config, **data)

    @override
    def save_xpansion_settings(self, settings: XpansionSettings) -> None:
        data = settings.model_dump()
        sensitivity = data.pop("sensitivity_config")
        values: dict[str, Any] = {
            "study_id": self._study_id,
            **data,
            "sensitivity_epsilon": sensitivity["epsilon"],
            "sensitivity_capex": sensitivity["capex"],
        }
        upsert_one(self._db_session, XPANSION_SETTINGS_TABLE, values)
        # Replace projection rows: delete existing, then insert the new list.
        self._db_session.execute(
            delete(XPANSION_SENSITIVITY_PROJECTION_TABLE).where(
                XPANSION_SENSITIVITY_PROJECTION_TABLE.c.study_id == self._study_id
            )
        )
        if sensitivity["projection"]:
            try:
                self._db_session.execute(
                    insert(XPANSION_SENSITIVITY_PROJECTION_TABLE),
                    [{"study_id": self._study_id, "candidate_name": name} for name in sensitivity["projection"]],
                )
            except IntegrityError:
                self._db_session.rollback()
                raise CandidateNotFoundError("One or more candidates in the projection do not exist")
        self._db_session.commit()

    @override
    def checks_xpansion_settings_are_correct(self, settings: XpansionSettingsUpdate) -> None:
        # TODO: validate additional_constraints and yearly_weights against blob storage
        #  once blob storage is wired up for database mode.
        if not settings.sensitivity_config or not settings.sensitivity_config.projection:
            return
        projection = settings.sensitivity_config.projection
        existing = {
            row.name
            for row in self._db_session.execute(
                select(XPANSION_CANDIDATE_TABLE.c.name).where(XPANSION_CANDIDATE_TABLE.c.study_id == self._study_id)
            ).fetchall()
        }
        missing = [name for name in projection if name not in existing]
        if missing:
            raise CandidateNotFoundError(f"Candidates not found: {', '.join(missing)}")

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
        """
        Upsert a candidate.

        ``old_id`` is the current name in storage and is only provided when renaming.

        All cases for ``save(bob, old_id="alice")``:
            - bob present, alice present => delete bob, update alice to bob.
            - bob absent, alice present => delete no op, update alice to bob.
            - bob present, alice absent => delete bob, update return 0, rollback, raise ``CandidateNotFoundError``.
            - neither present => delete no op, update return 0, rollback, raise ``CandidateNotFoundError``.

        Note : projections are updated because ON UPDATE CASCADE is used.
        """
        if old_id and old_id != candidate.name:
            self._db_session.execute(
                delete(XPANSION_CANDIDATE_TABLE).where(
                    (XPANSION_CANDIDATE_TABLE.c.study_id == self._study_id)
                    & (XPANSION_CANDIDATE_TABLE.c.name == candidate.name)
                )
            )
            result = self._db_session.execute(
                update(XPANSION_CANDIDATE_TABLE)
                .where(
                    (XPANSION_CANDIDATE_TABLE.c.study_id == self._study_id)
                    & (XPANSION_CANDIDATE_TABLE.c.name == old_id)
                )
                .values(self._candidate_to_row(candidate))
            )
            assert isinstance(result, CursorResult)
            if result.rowcount == 0:
                self._db_session.rollback()
                raise CandidateNotFoundError(f"The candidate '{old_id}' does not exist")
        else:
            upsert_one(self._db_session, XPANSION_CANDIDATE_TABLE, self._candidate_to_row(candidate))
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
        # TODO: validate link-profile fields (link_profile, direct_link_profile, etc.)
        #  against blob storage once blob storage is wired up for database mode.
        #  See FileStudyXpansionDao._assert_link_profile_are_files for the reference implementation.

    @override
    def checks_xpansion_candidate_can_be_deleted(self, candidate_name: str) -> None:
        stmt = select(XPANSION_SENSITIVITY_PROJECTION_TABLE.c.candidate_name).where(
            (XPANSION_SENSITIVITY_PROJECTION_TABLE.c.study_id == self._study_id)
            & (XPANSION_SENSITIVITY_PROJECTION_TABLE.c.candidate_name == candidate_name)
        )
        if self._db_session.execute(stmt).fetchone() is not None:
            raise XpansionCandidateDeletionError(self._study_id, candidate_name)

    # ------------------------------------------------------------------
    # XpansionDao — adequacy criterion
    # ------------------------------------------------------------------

    @override
    def get_xpansion_adequacy_criterion(self) -> XpansionAdequacyCriterion:
        stmt = (
            select(
                XPANSION_ADEQUACY_CRITERION_TABLE,
                XPANSION_ADEQUACY_PATTERN_TABLE.c.area,
                XPANSION_ADEQUACY_PATTERN_TABLE.c.criterion,
            )
            .outerjoin(
                XPANSION_ADEQUACY_PATTERN_TABLE,
                XPANSION_ADEQUACY_CRITERION_TABLE.c.study_id == XPANSION_ADEQUACY_PATTERN_TABLE.c.study_id,
            )
            .where(XPANSION_ADEQUACY_CRITERION_TABLE.c.study_id == self._study_id)
        )
        rows = self._db_session.execute(stmt).fetchall()
        if not rows:
            return XpansionAdequacyCriterion()

        patterns = [XpansionAdequacyPattern(area=r.area, criterion=r.criterion) for r in rows if r.area is not None]
        return XpansionAdequacyCriterion(
            stopping_threshold=rows[0].stopping_threshold,
            criterion_count_threshold=rows[0].criterion_count_threshold,
            patterns=patterns,
        )

    @override
    def save_xpansion_adequacy_criterion(self, criterion: XpansionAdequacyCriterion) -> None:
        if criterion.patterns:
            missing_areas = self.get_impl().get_invalid_area_ids([p.area for p in criterion.patterns])
            if missing_areas:
                raise AreaNotFound(*missing_areas)

        upsert_one(
            self._db_session,
            XPANSION_ADEQUACY_CRITERION_TABLE,
            {
                "study_id": self._study_id,
                "stopping_threshold": criterion.stopping_threshold,
                "criterion_count_threshold": criterion.criterion_count_threshold,
            },
        )
        # Replace all patterns: delete existing rows then insert the new ones.
        self._db_session.execute(
            delete(XPANSION_ADEQUACY_PATTERN_TABLE).where(XPANSION_ADEQUACY_PATTERN_TABLE.c.study_id == self._study_id)
        )
        if criterion.patterns:
            self._db_session.execute(
                insert(XPANSION_ADEQUACY_PATTERN_TABLE),
                [{"study_id": self._study_id, "area": p.area, "criterion": p.criterion} for p in criterion.patterns],
            )
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
