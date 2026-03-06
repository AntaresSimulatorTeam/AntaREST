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
    XpansionSettings,
)
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.dao.database.models.xpansion import (
    XPANSION_ADEQUACY_CRITERION_V2_TABLE,
    XPANSION_ADEQUACY_PATTERN_TABLE,
    XPANSION_CANDIDATE_TABLE,
    XPANSION_SENSITIVITY_PROJECTION_TABLE,
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
        # --- create ---
        dao.create_xpansion_configuration()

        with db_session:
            assert (
                db_session.execute(
                    select(XPANSION_SETTINGS_TABLE).where(XPANSION_SETTINGS_TABLE.c.study_id == dao.get_study_id())
                ).fetchone()
                is not None
            )
            assert (
                db_session.execute(
                    select(XPANSION_ADEQUACY_CRITERION_V2_TABLE).where(
                        XPANSION_ADEQUACY_CRITERION_V2_TABLE.c.study_id == dao.get_study_id()
                    )
                ).fetchone()
                is not None
            )

        # --- duplicate create raises ---
        with pytest.raises(XpansionConfigurationAlreadyExists):
            dao.create_xpansion_configuration()

    def test_delete_xpansion_configuration_removes_all_rows(self, db_session: Session, dao: DatabaseStudyDao) -> None:
        """Deleting the configuration should remove settings, candidates and adequacy rows."""
        # --- setup ---
        dao.create_xpansion_configuration()
        dao.save_area("Paris")
        dao.save_area("Lyon")
        dao.save_link(Link(area1="paris", area2="lyon"))
        dao.save_xpansion_candidate(_make_candidate("cand1", "lyon", "paris"))

        # --- delete ---
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
                    select(XPANSION_ADEQUACY_CRITERION_V2_TABLE).where(
                        XPANSION_ADEQUACY_CRITERION_V2_TABLE.c.study_id == dao.get_study_id()
                    )
                ).fetchone()
                is None
            )

        # --- delete non-existent raises ---
        with pytest.raises(XpansionConfigurationDoesNotExist):
            dao.delete_xpansion_configuration()


class TestXpansionSettings:
    """Tests for Xpansion settings CRUD operations."""

    def test_get_xpansion_settings_returns_defaults_after_create(self, dao: DatabaseStudyDao) -> None:
        """After creating a configuration, get_xpansion_settings should return default values."""
        # --- setup ---
        dao.create_xpansion_configuration()

        # --- defaults ---
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
        # --- setup ---
        dao.create_xpansion_configuration()
        # Projection candidates must exist before being referenced
        dao.save_xpansion_candidate(_make_candidate("cand_a", "x", "y"))
        dao.save_xpansion_candidate(_make_candidate("cand_b", "x", "y"))

        # --- round-trip ---
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

        # --- upsert ---
        dao.save_xpansion_settings(XpansionSettings(optimality_gap=10.0))
        result = dao.get_xpansion_settings()
        assert result.optimality_gap == 10.0

        # --- invalid projection ---
        settings = XpansionSettings(sensitivity_config=XpansionSensitivitySettings(projection=["cand_a", "ghost_cand"]))
        with pytest.raises(CandidateNotFoundError):
            dao.save_xpansion_settings(settings)

    def test_save_xpansion_settings_raises_for_unknown_projection_candidate(self, dao: DatabaseStudyDao) -> None:
        """save_xpansion_settings should raise CandidateNotFoundError when a projection name does not exist."""
        dao.create_xpansion_configuration()
        dao.save_xpansion_candidate(_make_candidate("existing_cand", "x", "y"))

        settings = XpansionSettings(
            sensitivity_config=XpansionSensitivitySettings(projection=["existing_cand", "ghost_cand"])
        )
        with pytest.raises(CandidateNotFoundError):
            dao.save_xpansion_settings(settings)


class TestXpansionCandidates:
    """Tests for Xpansion candidate CRUD operations."""

    def test_save_and_get_candidate(self, dao: DatabaseStudyDao) -> None:
        """Candidate CRUD: save, get, get unknown, upsert, get all."""
        # --- setup ---
        dao.create_xpansion_configuration()
        dao.save_area("Paris")
        dao.save_area("Lyon")
        dao.save_link(Link(area1="paris", area2="lyon"))

        # --- initially empty ---
        assert dao.get_all_xpansion_candidates() == []

        # --- save and get ---
        candidate = _make_candidate("my_candidate", "lyon", "paris", cost=2000.0)
        dao.save_xpansion_candidate(candidate)

        result = dao.get_xpansion_candidate("my_candidate")
        assert result.name == "my_candidate"
        assert result.annual_cost_per_mw == 2000.0
        assert result.link.area_from == "lyon"
        assert result.link.area_to == "paris"
        assert result.max_investment == 5000.0

        assert len(dao.get_all_xpansion_candidates()) == 1

        # --- get unknown raises ---
        with pytest.raises(CandidateNotFoundError):
            dao.get_xpansion_candidate("nonexistent")

        # --- upsert ---
        dao.save_xpansion_candidate(_make_candidate("my_candidate", "lyon", "paris", cost=9999.0))
        result = dao.get_xpansion_candidate("my_candidate")
        assert result.annual_cost_per_mw == 9999.0
        assert len(dao.get_all_xpansion_candidates()) == 1

    def test_get_all_candidates_returns_multiple_candidates(self, dao: DatabaseStudyDao) -> None:
        """get_all_xpansion_candidates should return all stored candidates."""
        # --- setup ---
        dao.create_xpansion_configuration()
        dao.save_area("Paris")
        dao.save_area("Lyon")
        dao.save_area("Bordeaux")
        dao.save_link(Link(area1="paris", area2="lyon"))
        dao.save_link(Link(area1="bordeaux", area2="paris"))

        # --- save and get all ---
        dao.save_xpansion_candidate(_make_candidate("cand1", "lyon", "paris"))
        dao.save_xpansion_candidate(_make_candidate("cand2", "bordeaux", "paris"))

        results = dao.get_all_xpansion_candidates()
        assert len(results) == 2
        assert {c.name for c in results} == {"cand1", "cand2"}

    def test_save_candidate_with_rename_replaces_row(self, dao: DatabaseStudyDao) -> None:
        """Renaming a candidate (old_id != new name) should delete the old row and insert a new one."""
        # --- setup ---
        dao.create_xpansion_configuration()
        dao.save_area("Paris")
        dao.save_area("Lyon")
        dao.save_link(Link(area1="paris", area2="lyon"))
        dao.save_xpansion_candidate(_make_candidate("old_name", "lyon", "paris"))

        # --- rename ---
        dao.save_xpansion_candidate(_make_candidate("new_name", "lyon", "paris"), old_id="old_name")

        candidates = dao.get_all_xpansion_candidates()
        assert len(candidates) == 1
        assert candidates[0].name == "new_name"

        with pytest.raises(CandidateNotFoundError):
            dao.get_xpansion_candidate("old_name")

    def test_delete_candidate(self, dao: DatabaseStudyDao) -> None:
        """delete_xpansion_candidate should remove the candidate; raise if not found."""
        # --- setup ---
        dao.create_xpansion_configuration()
        dao.save_area("Paris")
        dao.save_area("Lyon")
        dao.save_link(Link(area1="paris", area2="lyon"))
        dao.save_xpansion_candidate(_make_candidate("cand", "lyon", "paris"))

        # --- delete removes it ---
        dao.delete_xpansion_candidate("cand")
        assert dao.get_all_xpansion_candidates() == []

        # --- delete unknown raises ---
        with pytest.raises(CandidateNotFoundError):
            dao.delete_xpansion_candidate("nonexistent")

            # --- delete unknown raises ---
        with pytest.raises(CandidateNotFoundError):
            dao.delete_xpansion_candidate("cand")

    def test_checks_candidate_coherence(self, dao: DatabaseStudyDao) -> None:
        """checks_xpansion_candidate_coherence should raise for missing area or link, pass when valid."""
        # --- setup ---
        dao.create_xpansion_configuration()
        dao.save_area("Paris")
        dao.save_area("Lyon")

        # --- missing link raises ---
        with pytest.raises(LinkNotFound):
            dao.checks_xpansion_candidate_coherence(_make_candidate("cand", "lyon", "paris"))

        # --- missing area raises ---
        with pytest.raises(AreaNotFound):
            dao.checks_xpansion_candidate_coherence(_make_candidate("cand", "alpha", "paris"))

        # --- valid link passes ---
        dao.save_link(Link(area1="paris", area2="lyon"))
        dao.checks_xpansion_candidate_coherence(_make_candidate("cand", "lyon", "paris"))  # must not raise

    def test_checks_candidate_can_be_deleted(self, dao: DatabaseStudyDao) -> None:
        """checks_xpansion_candidate_can_be_deleted should raise if in projection, pass otherwise."""
        # --- setup ---
        dao.create_xpansion_configuration()
        dao.save_xpansion_candidate(_make_candidate("cand_a", "x", "y"))
        dao.save_xpansion_settings(
            XpansionSettings(sensitivity_config=XpansionSensitivitySettings(projection=["cand_a"]))
        )

        # --- raises if in projection ---
        with pytest.raises(XpansionCandidateDeletionError):
            dao.checks_xpansion_candidate_can_be_deleted("cand_a")

        # --- passes if not in projection ---
        dao.checks_xpansion_candidate_can_be_deleted("cand_b")  # must not raise


class TestXpansionAdequacyCriterion:
    """Tests for Xpansion adequacy criterion CRUD operations."""

    def test_get_adequacy_criterion_returns_default_when_no_row(self, dao: DatabaseStudyDao) -> None:
        """get_xpansion_adequacy_criterion should return default values whether or not a row exists."""
        # --- no configuration: returns default ---
        assert dao.get_xpansion_adequacy_criterion() == XpansionAdequacyCriterion()

        # --- after create: returns default row values ---
        dao.create_xpansion_configuration()
        result = dao.get_xpansion_adequacy_criterion()
        defaults = XpansionAdequacyCriterion()
        assert result.stopping_threshold == defaults.stopping_threshold
        assert result.criterion_count_threshold == defaults.criterion_count_threshold
        assert result.patterns == defaults.patterns

    def test_save_and_get_adequacy_criterion(self, dao: DatabaseStudyDao) -> None:
        """Adequacy criterion should round-trip, upsert, and raise for missing areas."""
        # --- setup ---
        dao.create_xpansion_configuration()
        dao.save_area("Paris")
        dao.save_area("Lyon")

        # --- round-trip with patterns ---
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
        assert {p.area: p.criterion for p in result.patterns} == {"paris": 0.9, "lyon": 0.7}

        # --- upsert clears patterns ---
        dao.save_xpansion_adequacy_criterion(XpansionAdequacyCriterion(stopping_threshold=999.0, patterns=[]))
        result = dao.get_xpansion_adequacy_criterion()
        assert result.stopping_threshold == 999.0
        assert result.patterns == []

        # --- raises for missing area ---
        with pytest.raises(AreaNotFound):
            dao.save_xpansion_adequacy_criterion(
                XpansionAdequacyCriterion(patterns=[XpansionAdequacyPattern(area="nonexistent", criterion=0.5)])
            )


class TestCascadeDelete:
    """Tests for cascade-delete behaviour when the Xpansion configuration is removed."""

    def test_cascade_delete_removes_all_related_rows(self, db_session: Session, dao: DatabaseStudyDao) -> None:
        """Deleting the configuration should cascade-delete candidates, projection, criterion and patterns."""
        # --- setup ---
        dao.create_xpansion_configuration()
        dao.save_area("Paris")
        dao.save_area("Lyon")
        dao.save_link(Link(area1="paris", area2="lyon"))
        dao.save_xpansion_candidate(_make_candidate("cand", "lyon", "paris"))
        dao.save_xpansion_settings(
            XpansionSettings(sensitivity_config=XpansionSensitivitySettings(projection=["cand"]))
        )
        dao.save_xpansion_adequacy_criterion(
            XpansionAdequacyCriterion(patterns=[XpansionAdequacyPattern(area="paris", criterion=1.0)])
        )

        # --- delete ---
        dao.delete_xpansion_configuration()

        # --- assert all rows gone ---
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
                    select(XPANSION_SENSITIVITY_PROJECTION_TABLE).where(
                        XPANSION_SENSITIVITY_PROJECTION_TABLE.c.study_id == dao.get_study_id()
                    )
                ).fetchall()
                == []
            )
            assert (
                db_session.execute(
                    select(XPANSION_ADEQUACY_CRITERION_V2_TABLE).where(
                        XPANSION_ADEQUACY_CRITERION_V2_TABLE.c.study_id == dao.get_study_id()
                    )
                ).fetchone()
                is None
            )
            assert (
                db_session.execute(
                    select(XPANSION_ADEQUACY_PATTERN_TABLE).where(
                        XPANSION_ADEQUACY_PATTERN_TABLE.c.study_id == dao.get_study_id()
                    )
                ).fetchall()
                == []
            )

    def test_recreate_configuration_after_delete(self, dao: DatabaseStudyDao) -> None:
        """After deleting a configuration, creating it again should succeed with fresh defaults."""
        # --- setup ---
        dao.create_xpansion_configuration()
        dao.save_xpansion_settings(XpansionSettings(optimality_gap=42.0))

        # --- delete and recreate ---
        dao.delete_xpansion_configuration()
        dao.create_xpansion_configuration()

        result = dao.get_xpansion_settings()
        assert result.optimality_gap == XpansionSettings().optimality_gap
