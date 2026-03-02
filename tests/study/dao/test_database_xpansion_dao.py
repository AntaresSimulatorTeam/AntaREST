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

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from antarest.core.exceptions import (
    AreaNotFound,
    CandidateNotFoundError,
    LinkNotFound,
    XpansionCandidateDeletionError,
    XpansionConfigurationAlreadyExists,
    XpansionConfigurationDoesNotExist,
)
from antarest.study.business.model.link_model import Link
from antarest.study.business.model.xpansion_model import (
    XpansionAdequacyCriterion,
    XpansionAdequacyPattern,
    XpansionCandidate,
    XpansionSensitivitySettings,
    XpansionSensitivitySettingsUpdate,
    XpansionSettings,
    XpansionSettingsUpdate,
)
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.dao.database.models.xpansion import (
    XPANSION_ADEQUACY_CRITERION_TABLE,
    XPANSION_CANDIDATE_TABLE,
    XPANSION_SETTINGS_TABLE,
)


def _make_candidate(name: str, area_from: str, area_to: str, cost: float = 1000.0) -> XpansionCandidate:
    """Helper to build a minimal XpansionCandidate using the max_investment format."""
    return XpansionCandidate(
        name=name,
        link=f"{area_from} - {area_to}",
        annual_cost_per_mw=cost,
        max_investment=5000.0,
    )


class TestXpansionConfiguration:
    """Tests for the Xpansion configuration lifecycle (create / delete)."""

    def test_create_xpansion_configuration_inserts_settings_and_adequacy_rows(
        self, db_session: Session, dao: DatabaseStudyDao
    ) -> None:
        """Creating a configuration should persist a settings row and an adequacy criterion row."""
        dao.create_xpansion_configuration()

        with db_session:
            settings_row = db_session.execute(
                select(XPANSION_SETTINGS_TABLE).where(XPANSION_SETTINGS_TABLE.c.study_id == dao.get_study_id())
            ).fetchone()
            assert settings_row is not None

            adequacy_row = db_session.execute(
                select(XPANSION_ADEQUACY_CRITERION_TABLE).where(
                    XPANSION_ADEQUACY_CRITERION_TABLE.c.study_id == dao.get_study_id()
                )
            ).fetchone()
            assert adequacy_row is not None

    def test_create_xpansion_configuration_raises_if_already_exists(self, dao: DatabaseStudyDao) -> None:
        """A second create call on the same study should raise XpansionConfigurationAlreadyExists."""
        dao.create_xpansion_configuration()

        with pytest.raises(XpansionConfigurationAlreadyExists):
            dao.create_xpansion_configuration()

    def test_delete_xpansion_configuration_removes_all_rows(self, db_session: Session, dao: DatabaseStudyDao) -> None:
        """Deleting the configuration should remove settings, candidates and adequacy rows."""
        dao.create_xpansion_configuration()
        dao.save_area("Paris")
        dao.save_area("Lyon")
        dao.save_link(Link(area1="paris", area2="lyon"))
        dao.save_xpansion_candidate(_make_candidate("cand1", "lyon", "paris"))

        dao.delete_xpansion_configuration()

        with db_session:
            assert (
                db_session.execute(
                    select(XPANSION_SETTINGS_TABLE).where(XPANSION_SETTINGS_TABLE.c.study_id == dao.get_study_id())
                ).fetchone()
                is None
            )
            assert (
                db_session.execute(
                    select(XPANSION_CANDIDATE_TABLE).where(XPANSION_CANDIDATE_TABLE.c.study_id == dao.get_study_id())
                ).fetchall()
                == []
            )
            assert (
                db_session.execute(
                    select(XPANSION_ADEQUACY_CRITERION_TABLE).where(
                        XPANSION_ADEQUACY_CRITERION_TABLE.c.study_id == dao.get_study_id()
                    )
                ).fetchone()
                is None
            )

    def test_delete_xpansion_configuration_raises_if_does_not_exist(self, dao: DatabaseStudyDao) -> None:
        """Deleting a non-existent configuration should raise XpansionConfigurationDoesNotExist."""
        with pytest.raises(XpansionConfigurationDoesNotExist):
            dao.delete_xpansion_configuration()


class TestXpansionSettings:
    """Tests for Xpansion settings CRUD operations."""

    def test_get_xpansion_settings_returns_defaults_after_create(self, dao: DatabaseStudyDao) -> None:
        """After creating a configuration, get_xpansion_settings should return default values."""
        dao.create_xpansion_configuration()

        result = dao.get_xpansion_settings()
        defaults = XpansionSettings()

        assert result.master == defaults.master
        assert result.uc_type == defaults.uc_type
        assert result.optimality_gap == defaults.optimality_gap
        assert result.max_iteration == defaults.max_iteration
        assert result.solver == defaults.solver
        assert result.yearly_weights == defaults.yearly_weights
        assert result.additional_constraints == defaults.additional_constraints
        assert result.sensitivity_config.epsilon == defaults.sensitivity_config.epsilon
        assert result.sensitivity_config.capex == defaults.sensitivity_config.capex
        assert result.sensitivity_config.projection == defaults.sensitivity_config.projection

    def test_get_xpansion_settings_raises_if_no_configuration(self, dao: DatabaseStudyDao) -> None:
        """get_xpansion_settings should raise XpansionConfigurationDoesNotExist when missing."""
        with pytest.raises(XpansionConfigurationDoesNotExist):
            dao.get_xpansion_settings()

    def test_save_xpansion_settings_persists_non_default_values(self, dao: DatabaseStudyDao) -> None:
        """save_xpansion_settings should persist all non-default values and allow retrieval."""
        dao.create_xpansion_configuration()

        updated = XpansionSettings(
            optimality_gap=42.0,
            max_iteration=500,
            log_level=2,
            yearly_weights="weights.csv",
            additional_constraints="constraints.txt",
            sensitivity_config=XpansionSensitivitySettings(
                epsilon=100.0,
                capex=True,
                projection=["cand_a", "cand_b"],
            ),
        )
        dao.save_xpansion_settings(updated)

        result = dao.get_xpansion_settings()
        assert result.optimality_gap == 42.0
        assert result.max_iteration == 500
        assert result.log_level == 2
        assert result.yearly_weights == "weights.csv"
        assert result.additional_constraints == "constraints.txt"
        assert result.sensitivity_config.epsilon == 100.0
        assert result.sensitivity_config.capex is True
        assert result.sensitivity_config.projection == ["cand_a", "cand_b"]

    def test_save_xpansion_settings_upserts_existing_row(self, dao: DatabaseStudyDao) -> None:
        """Calling save_xpansion_settings twice should update the existing row."""
        dao.create_xpansion_configuration()

        dao.save_xpansion_settings(XpansionSettings(optimality_gap=10.0))
        dao.save_xpansion_settings(XpansionSettings(optimality_gap=99.0))

        result = dao.get_xpansion_settings()
        assert result.optimality_gap == 99.0

    def test_save_xpansion_settings_empty_strings_round_trip(self, dao: DatabaseStudyDao) -> None:
        """Empty strings for yearly_weights / additional_constraints should round-trip as empty strings."""
        dao.create_xpansion_configuration()

        # First store non-empty values, then overwrite with empty strings.
        dao.save_xpansion_settings(
            XpansionSettings(yearly_weights="weights.csv", additional_constraints="constraints.txt")
        )
        dao.save_xpansion_settings(XpansionSettings(yearly_weights="", additional_constraints=""))

        result = dao.get_xpansion_settings()
        assert result.yearly_weights == ""
        assert result.additional_constraints == ""


class TestXpansionCandidates:
    """Tests for Xpansion candidate CRUD operations."""

    def test_get_all_candidates_returns_empty_list_initially(self, dao: DatabaseStudyDao) -> None:
        """get_all_xpansion_candidates should return an empty list when no candidates exist."""
        dao.create_xpansion_configuration()

        assert dao.get_all_xpansion_candidates() == []

    def test_save_and_get_candidate(self, dao: DatabaseStudyDao) -> None:
        """A saved candidate should be retrievable by name with all fields intact."""
        dao.create_xpansion_configuration()
        dao.save_area("Paris")
        dao.save_area("Lyon")
        dao.save_link(Link(area1="paris", area2="lyon"))

        candidate = _make_candidate("my_candidate", "lyon", "paris", cost=2000.0)
        dao.save_xpansion_candidate(candidate)

        result = dao.get_xpansion_candidate("my_candidate")
        assert result.name == "my_candidate"
        assert result.annual_cost_per_mw == 2000.0
        assert result.link.area_from == "lyon"
        assert result.link.area_to == "paris"
        assert result.max_investment == 5000.0

    def test_get_candidate_raises_if_not_found(self, dao: DatabaseStudyDao) -> None:
        """get_xpansion_candidate should raise CandidateNotFoundError for an unknown name."""
        dao.create_xpansion_configuration()

        with pytest.raises(CandidateNotFoundError):
            dao.get_xpansion_candidate("nonexistent")

    def test_save_candidate_upserts_on_same_name(self, dao: DatabaseStudyDao) -> None:
        """Saving a candidate with the same name a second time should update it (upsert)."""
        dao.create_xpansion_configuration()
        dao.save_area("Paris")
        dao.save_area("Lyon")
        dao.save_link(Link(area1="paris", area2="lyon"))

        dao.save_xpansion_candidate(_make_candidate("cand", "lyon", "paris", cost=1000.0))
        dao.save_xpansion_candidate(_make_candidate("cand", "lyon", "paris", cost=9999.0))

        result = dao.get_xpansion_candidate("cand")
        assert result.annual_cost_per_mw == 9999.0
        assert len(dao.get_all_xpansion_candidates()) == 1

    def test_save_candidate_with_rename_replaces_row(self, dao: DatabaseStudyDao) -> None:
        """Renaming a candidate (old_id != new name) should delete the old row and insert a new one."""
        dao.create_xpansion_configuration()
        dao.save_area("Paris")
        dao.save_area("Lyon")
        dao.save_link(Link(area1="paris", area2="lyon"))

        dao.save_xpansion_candidate(_make_candidate("old_name", "lyon", "paris"))
        dao.save_xpansion_candidate(_make_candidate("new_name", "lyon", "paris"), old_id="old_name")

        candidates = dao.get_all_xpansion_candidates()
        assert len(candidates) == 1
        assert candidates[0].name == "new_name"

        with pytest.raises(CandidateNotFoundError):
            dao.get_xpansion_candidate("old_name")

    def test_delete_candidate_removes_it(self, dao: DatabaseStudyDao) -> None:
        """delete_xpansion_candidate should remove the candidate from the database."""
        dao.create_xpansion_configuration()
        dao.save_area("Paris")
        dao.save_area("Lyon")
        dao.save_link(Link(area1="paris", area2="lyon"))

        dao.save_xpansion_candidate(_make_candidate("cand", "lyon", "paris"))
        dao.delete_xpansion_candidate("cand")

        assert dao.get_all_xpansion_candidates() == []

    def test_delete_candidate_raises_if_not_found(self, dao: DatabaseStudyDao) -> None:
        """delete_xpansion_candidate should raise CandidateNotFoundError for an unknown name."""
        dao.create_xpansion_configuration()

        with pytest.raises(CandidateNotFoundError):
            dao.delete_xpansion_candidate("nonexistent")

    def test_get_all_candidates_returns_multiple_candidates(self, dao: DatabaseStudyDao) -> None:
        """get_all_xpansion_candidates should return all stored candidates."""
        dao.create_xpansion_configuration()
        dao.save_area("Paris")
        dao.save_area("Lyon")
        dao.save_area("Bordeaux")
        dao.save_link(Link(area1="paris", area2="lyon"))
        dao.save_link(Link(area1="bordeaux", area2="paris"))

        dao.save_xpansion_candidate(_make_candidate("cand1", "lyon", "paris"))
        dao.save_xpansion_candidate(_make_candidate("cand2", "bordeaux", "paris"))

        results = dao.get_all_xpansion_candidates()
        assert len(results) == 2
        assert {c.name for c in results} == {"cand1", "cand2"}

    def test_checks_candidate_coherence_raises_for_missing_link(self, dao: DatabaseStudyDao) -> None:
        """checks_xpansion_candidate_coherence should raise LinkNotFound when the link is absent."""
        dao.create_xpansion_configuration()
        dao.save_area("Paris")
        dao.save_area("Lyon")
        # Link between paris and lyon deliberately NOT created.

        candidate = _make_candidate("cand", "lyon", "paris")
        with pytest.raises(LinkNotFound):
            dao.checks_xpansion_candidate_coherence(candidate)

    def test_checks_candidate_coherence_raises_for_missing_area_from(self, dao: DatabaseStudyDao) -> None:
        """checks_xpansion_candidate_coherence should raise AreaNotFound when area_from is absent.

        XpansionLink sorts areas alphabetically, so area_from < area_to.
        "alpha" < "paris" → area_from="alpha" (missing), area_to="paris" (exists).
        """
        dao.create_xpansion_configuration()
        dao.save_area("Paris")
        # area_from ("alpha") not saved.

        candidate = _make_candidate("cand", "alpha", "paris")
        with pytest.raises(AreaNotFound, match="alpha"):
            dao.checks_xpansion_candidate_coherence(candidate)

    def test_checks_candidate_coherence_raises_for_missing_area_to(self, dao: DatabaseStudyDao) -> None:
        """checks_xpansion_candidate_coherence should raise AreaNotFound when area_to is absent.

        XpansionLink sorts areas alphabetically, so area_from < area_to.
        "paris" < "zz_missing" → area_from="paris" (exists), area_to="zz_missing" (missing).
        """
        dao.create_xpansion_configuration()
        dao.save_area("Paris")
        # area_to ("zz_missing") not saved.

        candidate = _make_candidate("cand", "paris", "zz_missing")
        with pytest.raises(AreaNotFound, match="zz_missing"):
            dao.checks_xpansion_candidate_coherence(candidate)

    def test_checks_candidate_coherence_passes_for_valid_link(self, dao: DatabaseStudyDao) -> None:
        """checks_xpansion_candidate_coherence should not raise when the link exists."""
        dao.create_xpansion_configuration()
        dao.save_area("Paris")
        dao.save_area("Lyon")
        dao.save_link(Link(area1="paris", area2="lyon"))

        candidate = _make_candidate("cand", "lyon", "paris")
        dao.checks_xpansion_candidate_coherence(candidate)  # must not raise

    def test_checks_settings_correct_raises_for_unknown_projection_candidate(self, dao: DatabaseStudyDao) -> None:
        """checks_xpansion_settings_are_correct should raise CandidateNotFoundError for unknown projection names."""
        dao.create_xpansion_configuration()
        dao.save_area("Paris")
        dao.save_area("Lyon")
        dao.save_link(Link(area1="paris", area2="lyon"))
        dao.save_xpansion_candidate(_make_candidate("existing_cand", "lyon", "paris"))

        settings_update = XpansionSettingsUpdate(
            sensitivity_config=XpansionSensitivitySettingsUpdate(projection=["existing_cand", "ghost_cand"])
        )
        with pytest.raises(CandidateNotFoundError, match="ghost_cand"):
            dao.checks_xpansion_settings_are_correct(settings_update)

    def test_checks_settings_correct_passes_for_valid_projection(self, dao: DatabaseStudyDao) -> None:
        """checks_xpansion_settings_are_correct should succeed when all projection names exist."""
        dao.create_xpansion_configuration()
        dao.save_area("Paris")
        dao.save_area("Lyon")
        dao.save_link(Link(area1="paris", area2="lyon"))
        dao.save_xpansion_candidate(_make_candidate("cand_a", "lyon", "paris"))
        dao.save_xpansion_candidate(_make_candidate("cand_b", "lyon", "paris", cost=500.0))

        settings_update = XpansionSettingsUpdate(
            sensitivity_config=XpansionSensitivitySettingsUpdate(projection=["cand_a", "cand_b"])
        )
        dao.checks_xpansion_settings_are_correct(settings_update)  # must not raise

    def test_checks_settings_correct_passes_when_projection_is_none(self, dao: DatabaseStudyDao) -> None:
        """checks_xpansion_settings_are_correct should not validate projection when it is None."""
        dao.create_xpansion_configuration()
        settings_update = XpansionSettingsUpdate(sensitivity_config=XpansionSensitivitySettingsUpdate(projection=None))
        dao.checks_xpansion_settings_are_correct(settings_update)  # must not raise

    def test_checks_candidate_can_be_deleted_raises_if_in_projection(self, dao: DatabaseStudyDao) -> None:
        """checks_xpansion_candidate_can_be_deleted should raise when candidate is in sensitivity projection."""
        dao.create_xpansion_configuration()
        dao.save_xpansion_settings(
            XpansionSettings(sensitivity_config=XpansionSensitivitySettings(projection=["cand_a", "cand_b"]))
        )

        with pytest.raises(XpansionCandidateDeletionError):
            dao.checks_xpansion_candidate_can_be_deleted("cand_a")

    def test_checks_candidate_can_be_deleted_passes_if_not_in_projection(self, dao: DatabaseStudyDao) -> None:
        """checks_xpansion_candidate_can_be_deleted should succeed when candidate is absent from projection."""
        dao.create_xpansion_configuration()
        dao.save_xpansion_settings(
            XpansionSettings(sensitivity_config=XpansionSensitivitySettings(projection=["cand_a"]))
        )

        dao.checks_xpansion_candidate_can_be_deleted("cand_b")  # must not raise


class TestXpansionAdequacyCriterion:
    """Tests for Xpansion adequacy criterion CRUD operations."""

    def test_get_adequacy_criterion_returns_defaults_after_create(self, dao: DatabaseStudyDao) -> None:
        """After creating a configuration, adequacy criterion should hold default values."""
        dao.create_xpansion_configuration()

        result = dao.get_xpansion_adequacy_criterion()
        defaults = XpansionAdequacyCriterion()

        assert result.stopping_threshold == defaults.stopping_threshold
        assert result.criterion_count_threshold == defaults.criterion_count_threshold
        assert result.patterns == defaults.patterns

    def test_get_adequacy_criterion_returns_empty_default_when_no_row(self, dao: DatabaseStudyDao) -> None:
        """get_xpansion_adequacy_criterion should return an empty default when no row is stored."""
        # No create_xpansion_configuration() call.
        result = dao.get_xpansion_adequacy_criterion()
        assert result == XpansionAdequacyCriterion()

    def test_save_and_get_adequacy_criterion_with_patterns(self, dao: DatabaseStudyDao) -> None:
        """Adequacy criterion with patterns should round-trip correctly through the database."""
        dao.create_xpansion_configuration()
        dao.save_area("Paris")
        dao.save_area("Lyon")

        criterion = XpansionAdequacyCriterion(
            stopping_threshold=500.0,
            criterion_count_threshold=2.5,
            patterns=[
                XpansionAdequacyPattern(area="paris", criterion=0.9),
                XpansionAdequacyPattern(area="lyon", criterion=0.7),
            ],
        )
        dao.save_xpansion_adequacy_criterion(criterion)

        result = dao.get_xpansion_adequacy_criterion()
        assert result.stopping_threshold == 500.0
        assert result.criterion_count_threshold == 2.5
        assert len(result.patterns) == 2
        areas_and_criteria = {p.area: p.criterion for p in result.patterns}
        assert areas_and_criteria == {"paris": 0.9, "lyon": 0.7}

    def test_save_adequacy_criterion_upserts_existing_row(self, dao: DatabaseStudyDao) -> None:
        """Calling save_xpansion_adequacy_criterion twice should update the existing row."""
        dao.create_xpansion_configuration()
        dao.save_area("Paris")

        dao.save_xpansion_adequacy_criterion(
            XpansionAdequacyCriterion(
                stopping_threshold=100.0,
                patterns=[XpansionAdequacyPattern(area="paris", criterion=1.0)],
            )
        )
        dao.save_xpansion_adequacy_criterion(XpansionAdequacyCriterion(stopping_threshold=999.0, patterns=[]))

        result = dao.get_xpansion_adequacy_criterion()
        assert result.stopping_threshold == 999.0
        assert result.patterns == []

    def test_save_adequacy_criterion_raises_for_missing_area(self, dao: DatabaseStudyDao) -> None:
        """save_xpansion_adequacy_criterion should raise AreaNotFound when a pattern area does not exist."""
        dao.create_xpansion_configuration()

        criterion = XpansionAdequacyCriterion(patterns=[XpansionAdequacyPattern(area="nonexistent", criterion=0.5)])
        with pytest.raises(AreaNotFound):
            dao.save_xpansion_adequacy_criterion(criterion)


class TestCascadeDelete:
    """Tests for cascade-delete behaviour when the Xpansion configuration is removed."""

    def test_cascade_delete_removes_candidates(self, db_session: Session, dao: DatabaseStudyDao) -> None:
        """Deleting the Xpansion configuration should cascade-delete all candidate rows."""
        dao.create_xpansion_configuration()
        dao.save_area("Paris")
        dao.save_area("Lyon")
        dao.save_link(Link(area1="paris", area2="lyon"))

        dao.save_xpansion_candidate(_make_candidate("cand1", "lyon", "paris"))
        dao.save_xpansion_candidate(_make_candidate("cand2", "lyon", "paris", cost=500.0))

        dao.delete_xpansion_configuration()

        with db_session:
            rows = db_session.execute(
                select(XPANSION_CANDIDATE_TABLE).where(XPANSION_CANDIDATE_TABLE.c.study_id == dao.get_study_id())
            ).fetchall()
            assert rows == []

    def test_cascade_delete_removes_adequacy_criterion(self, db_session: Session, dao: DatabaseStudyDao) -> None:
        """Deleting the Xpansion configuration should cascade-delete the adequacy criterion row."""
        dao.create_xpansion_configuration()
        dao.save_area("Paris")
        dao.save_xpansion_adequacy_criterion(
            XpansionAdequacyCriterion(patterns=[XpansionAdequacyPattern(area="paris", criterion=1.0)])
        )

        dao.delete_xpansion_configuration()

        with db_session:
            row = db_session.execute(
                select(XPANSION_ADEQUACY_CRITERION_TABLE).where(
                    XPANSION_ADEQUACY_CRITERION_TABLE.c.study_id == dao.get_study_id()
                )
            ).fetchone()
            assert row is None

    def test_recreate_configuration_after_delete(self, dao: DatabaseStudyDao) -> None:
        """After deleting a configuration, creating it again should succeed with fresh defaults."""
        dao.create_xpansion_configuration()
        dao.save_xpansion_settings(XpansionSettings(optimality_gap=42.0))

        dao.delete_xpansion_configuration()
        dao.create_xpansion_configuration()

        result = dao.get_xpansion_settings()
        assert result.optimality_gap == XpansionSettings().optimality_gap
