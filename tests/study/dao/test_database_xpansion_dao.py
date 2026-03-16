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
from sqlalchemy import Table, select
from sqlalchemy.orm import Session

from antarest.core.exceptions import (
    AreaNotFound,
    CandidateNotFoundError,
    LinkNotFound,
    XpansionCandidateDeletionError,
    XpansionConfigurationAlreadyExists,
    XpansionConfigurationDoesNotExist,
)
from antarest.matrixstore.service import ISimpleMatrixService
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
    XPANSION_ADEQUACY_PATTERN_TABLE,
    XPANSION_CANDIDATE_TABLE,
    XPANSION_SENSITIVITY_PROJECTION_TABLE,
    XPANSION_SETTINGS_TABLE,
)
from antarest.study.model import STUDY_VERSION_8_8
from tests.study.dao.conftest import build_db_dao


def _assert_tables_empty(db_session: Session, tables: list[Table], study_id: str) -> None:
    for table in tables:
        rows = db_session.execute(select(table).where(table.c.study_id == study_id)).fetchall()
        assert rows == [], f"{table.name}: expected no rows for study {study_id}, found {len(rows)}"


def _assert_tables_have_row(db_session: Session, tables: list[Table], study_id: str) -> None:
    for table in tables:
        row = db_session.execute(select(table).where(table.c.study_id == study_id)).fetchone()
        assert row is not None, f"{table.name}: expected a row for study {study_id}"


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
        self, db_session: Session, db_dao: DatabaseStudyDao
    ) -> None:
        """Creating a configuration should persist a settings row and an adequacy criterion row."""
        # --- create ---
        db_dao.create_xpansion_configuration()

        with db_session:
            _assert_tables_have_row(
                db_session, [XPANSION_SETTINGS_TABLE, XPANSION_ADEQUACY_CRITERION_TABLE], db_dao.get_study_id()
            )

        # --- duplicate create raises ---
        with pytest.raises(XpansionConfigurationAlreadyExists):
            db_dao.create_xpansion_configuration()

    def test_delete_xpansion_configuration_removes_all_rows(
        self, db_session: Session, db_dao: DatabaseStudyDao
    ) -> None:
        """Deleting the configuration should remove settings, candidates and adequacy rows."""
        # --- setup ---
        db_dao.create_xpansion_configuration()
        db_dao.save_area("Paris")
        db_dao.save_area("Lyon")
        db_dao.save_link(Link(area1="paris", area2="lyon"))
        db_dao.save_xpansion_candidate(_make_candidate("cand1", "lyon", "paris"))

        # --- delete ---
        db_dao.delete_xpansion_configuration()

        with db_session:
            _assert_tables_empty(
                db_session,
                [XPANSION_SETTINGS_TABLE, XPANSION_CANDIDATE_TABLE, XPANSION_ADEQUACY_CRITERION_TABLE],
                db_dao.get_study_id(),
            )

        # --- delete non-existent raises ---
        with pytest.raises(XpansionConfigurationDoesNotExist):
            db_dao.delete_xpansion_configuration()


class TestXpansionSettings:
    """Tests for Xpansion settings CRUD operations."""

    def test_get_xpansion_settings_returns_defaults_after_create(self, db_dao: DatabaseStudyDao) -> None:
        """After creating a configuration, get_xpansion_settings should return default values."""
        # --- setup ---
        db_dao.create_xpansion_configuration()

        # --- defaults ---
        result = db_dao.get_xpansion_settings()
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

    def test_get_xpansion_settings_raises_if_no_configuration(self, db_dao: DatabaseStudyDao) -> None:
        """get_xpansion_settings should raise XpansionConfigurationDoesNotExist when missing."""
        with pytest.raises(XpansionConfigurationDoesNotExist):
            db_dao.get_xpansion_settings()

    def test_save_xpansion_settings_persists_non_default_values(self, db_dao: DatabaseStudyDao) -> None:
        """save_xpansion_settings should persist all non-default values and allow retrieval."""
        # --- setup ---
        db_dao.create_xpansion_configuration()
        db_dao.save_area("x")
        db_dao.save_area("y")
        db_dao.save_link(Link(area1="x", area2="y"))
        # Projection candidates must exist before being referenced
        db_dao.save_xpansion_candidate(_make_candidate("cand_a", "x", "y"))
        db_dao.save_xpansion_candidate(_make_candidate("cand_b", "x", "y"))

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
        db_dao.save_xpansion_settings(updated)

        result = db_dao.get_xpansion_settings()
        assert result.optimality_gap == 42.0
        assert result.max_iteration == 500
        assert result.log_level == 2
        assert result.yearly_weights == "weights.csv"
        assert result.additional_constraints == "constraints.txt"
        assert result.sensitivity_config.epsilon == 100.0
        assert result.sensitivity_config.capex is True
        assert result.sensitivity_config.projection == ["cand_a", "cand_b"]

        # --- upsert ---
        db_dao.save_xpansion_settings(XpansionSettings(optimality_gap=10.0))
        result = db_dao.get_xpansion_settings()
        assert result.optimality_gap == 10.0

        # --- invalid projection ---
        settings = XpansionSettings(sensitivity_config=XpansionSensitivitySettings(projection=["cand_a", "ghost_cand"]))
        with pytest.raises(CandidateNotFoundError):
            db_dao.save_xpansion_settings(settings)

    def test_save_xpansion_settings_raises_for_unknown_projection_candidate(self, db_dao: DatabaseStudyDao) -> None:
        """save_xpansion_settings should raise CandidateNotFoundError when a projection name does not exist."""
        db_dao.create_xpansion_configuration()
        db_dao.save_area("x")
        db_dao.save_area("y")
        db_dao.save_link(Link(area1="x", area2="y"))
        db_dao.save_xpansion_candidate(_make_candidate("existing_cand", "x", "y"))

        settings = XpansionSettings(
            sensitivity_config=XpansionSensitivitySettings(projection=["existing_cand", "ghost_cand"])
        )
        with pytest.raises(CandidateNotFoundError):
            db_dao.save_xpansion_settings(settings)

    def test_checks_xpansion_settings_correct(self, db_dao: DatabaseStudyDao) -> None:
        """checks_xpansion_settings_are_correct should validate projection candidate existence."""
        # --- setup ---
        db_dao.create_xpansion_configuration()
        db_dao.save_area("Paris")
        db_dao.save_area("Lyon")
        db_dao.save_link(Link(area1="paris", area2="lyon"))
        db_dao.save_xpansion_candidate(_make_candidate("existing_cand", "lyon", "paris"))
        db_dao.save_xpansion_candidate(_make_candidate("cand_b", "lyon", "paris", cost=500.0))

        # --- unknown projection candidate raises ---
        with pytest.raises(CandidateNotFoundError, match="ghost_cand"):
            db_dao.checks_xpansion_settings_are_correct(
                XpansionSettingsUpdate(
                    sensitivity_config=XpansionSensitivitySettingsUpdate(projection=["existing_cand", "ghost_cand"])
                )
            )

        # --- valid projection passes ---
        db_dao.checks_xpansion_settings_are_correct(
            XpansionSettingsUpdate(
                sensitivity_config=XpansionSensitivitySettingsUpdate(projection=["existing_cand", "cand_b"])
            )
        )  # must not raise

        # --- None projection skips validation ---
        db_dao.checks_xpansion_settings_are_correct(
            XpansionSettingsUpdate(sensitivity_config=XpansionSensitivitySettingsUpdate(projection=None))
        )  # must not raise


class TestXpansionCandidates:
    """Tests for Xpansion candidate CRUD operations."""

    def test_save_and_get_candidate(self, db_dao: DatabaseStudyDao) -> None:
        """Candidate CRUD: save, get, get unknown, upsert, get all."""
        # --- setup ---
        db_dao.create_xpansion_configuration()
        db_dao.save_area("Paris")
        db_dao.save_area("Lyon")
        db_dao.save_link(Link(area1="paris", area2="lyon"))

        # --- initially empty ---
        assert db_dao.get_all_xpansion_candidates() == []

        # --- save and get ---
        candidate = _make_candidate("my_candidate", "lyon", "paris", cost=2000.0)
        db_dao.save_xpansion_candidate(candidate)

        result = db_dao.get_xpansion_candidate("my_candidate")
        assert result.name == "my_candidate"
        assert result.annual_cost_per_mw == 2000.0
        assert result.link.area_from == "lyon"
        assert result.link.area_to == "paris"
        assert result.max_investment == 5000.0

        assert len(db_dao.get_all_xpansion_candidates()) == 1

        # --- get unknown raises ---
        with pytest.raises(CandidateNotFoundError):
            db_dao.get_xpansion_candidate("nonexistent")

        # --- upsert ---
        db_dao.save_xpansion_candidate(_make_candidate("my_candidate", "lyon", "paris", cost=9999.0))
        result = db_dao.get_xpansion_candidate("my_candidate")
        assert result.annual_cost_per_mw == 9999.0
        assert len(db_dao.get_all_xpansion_candidates()) == 1

    def test_get_all_candidates_returns_multiple_candidates(self, db_dao: DatabaseStudyDao) -> None:
        """get_all_xpansion_candidates should return all stored candidates."""
        # --- setup ---
        db_dao.create_xpansion_configuration()
        db_dao.save_area("Paris")
        db_dao.save_area("Lyon")
        db_dao.save_area("Bordeaux")
        db_dao.save_link(Link(area1="paris", area2="lyon"))
        db_dao.save_link(Link(area1="bordeaux", area2="paris"))

        # --- save and get all ---
        db_dao.save_xpansion_candidate(_make_candidate("cand1", "lyon", "paris"))
        db_dao.save_xpansion_candidate(_make_candidate("cand2", "bordeaux", "paris"))

        results = db_dao.get_all_xpansion_candidates()
        assert len(results) == 2
        assert {c.name for c in results} == {"cand1", "cand2"}

    def test_save_candidate_with_rename_replaces_row(self, db_dao: DatabaseStudyDao) -> None:
        """Renaming a candidate covers: basic rename, nonexistent old_id, overwrite existing target, projection transfer."""
        db_dao.create_xpansion_configuration()
        db_dao.save_area("x")
        db_dao.save_area("y")
        db_dao.save_link(Link(area1="x", area2="y"))
        db_dao.save_xpansion_candidate(_make_candidate("alice", "x", "y", cost=1000.0))
        db_dao.save_xpansion_candidate(_make_candidate("bob", "x", "y", cost=2000.0))
        db_dao.save_xpansion_settings(
            XpansionSettings(sensitivity_config=XpansionSensitivitySettings(projection=["alice", "bob"]))
        )

        # --- nonexistent old_id raises ---
        with pytest.raises(CandidateNotFoundError):
            db_dao.save_xpansion_candidate(_make_candidate("alice", "x", "y"), old_id="ghost")

        # --- basic rename: old row gone, new row present ---
        db_dao.save_xpansion_candidate(_make_candidate("charlie", "x", "y", cost=1000.0), old_id="alice")
        assert db_dao.get_xpansion_candidate("charlie").annual_cost_per_mw == 1000.0
        with pytest.raises(CandidateNotFoundError):
            db_dao.get_xpansion_candidate("alice")

        # --- projection carried over: charlie in, alice out ---
        settings = db_dao.get_xpansion_settings()
        assert "charlie" in settings.sensitivity_config.projection
        assert "alice" not in settings.sensitivity_config.projection

        # --- rename to existing target overwrites it, no duplicate projection ---
        db_dao.save_xpansion_candidate(_make_candidate("bob", "x", "y", cost=999.0), old_id="charlie")
        assert len(db_dao.get_all_xpansion_candidates()) == 1
        assert db_dao.get_xpansion_candidate("bob").annual_cost_per_mw == 999.0
        settings = db_dao.get_xpansion_settings()
        assert settings.sensitivity_config.projection.count("bob") == 1
        assert "charlie" not in settings.sensitivity_config.projection

    def test_delete_candidate(self, db_dao: DatabaseStudyDao) -> None:
        """delete_xpansion_candidate should remove the candidate; raise if not found."""
        # --- setup ---
        db_dao.create_xpansion_configuration()
        db_dao.save_area("Paris")
        db_dao.save_area("Lyon")
        db_dao.save_link(Link(area1="paris", area2="lyon"))
        db_dao.save_xpansion_candidate(_make_candidate("cand", "lyon", "paris"))

        # --- delete removes it ---
        db_dao.delete_xpansion_candidate("cand")
        assert db_dao.get_all_xpansion_candidates() == []

        # --- delete unknown raises ---
        with pytest.raises(CandidateNotFoundError):
            db_dao.delete_xpansion_candidate("nonexistent")

        with pytest.raises(CandidateNotFoundError):
            db_dao.delete_xpansion_candidate("cand")

    def test_deleting_link_cascades_to_candidates(self, db_dao: DatabaseStudyDao) -> None:
        """Deleting a link should cascade-delete all candidates referencing it."""
        db_dao.create_xpansion_configuration()
        db_dao.save_area("Paris")
        db_dao.save_area("Lyon")
        db_dao.save_link(Link(area1="paris", area2="lyon"))
        db_dao.save_xpansion_candidate(_make_candidate("cand1", "lyon", "paris"))
        db_dao.save_xpansion_candidate(_make_candidate("cand2", "lyon", "paris"))

        db_dao.delete_link(Link(area1="paris", area2="lyon"))

        assert db_dao.get_all_xpansion_candidates() == []

    def test_checks_candidate_coherence(self, db_dao: DatabaseStudyDao) -> None:
        """checks_xpansion_candidate_coherence should raise for missing area or link, pass when valid."""
        # --- setup ---
        db_dao.create_xpansion_configuration()
        db_dao.save_area("Paris")
        db_dao.save_area("Lyon")

        # --- missing link raises ---
        with pytest.raises(LinkNotFound):
            db_dao.checks_xpansion_candidate_coherence(_make_candidate("cand", "lyon", "paris"))

        # --- missing area raises ---
        with pytest.raises(AreaNotFound):
            db_dao.checks_xpansion_candidate_coherence(_make_candidate("cand", "alpha", "paris"))

        # --- valid link passes ---
        db_dao.save_link(Link(area1="paris", area2="lyon"))
        db_dao.checks_xpansion_candidate_coherence(_make_candidate("cand", "lyon", "paris"))  # must not raise

    def test_checks_candidate_can_be_deleted(self, db_dao: DatabaseStudyDao) -> None:
        """checks_xpansion_candidate_can_be_deleted should raise if in projection, pass otherwise."""
        # --- setup ---
        db_dao.create_xpansion_configuration()
        db_dao.save_area("x")
        db_dao.save_area("y")
        db_dao.save_link(Link(area1="x", area2="y"))
        db_dao.save_xpansion_candidate(_make_candidate("cand_a", "x", "y"))
        db_dao.save_xpansion_settings(
            XpansionSettings(sensitivity_config=XpansionSensitivitySettings(projection=["cand_a"]))
        )

        # --- raises if in projection ---
        with pytest.raises(XpansionCandidateDeletionError):
            db_dao.checks_xpansion_candidate_can_be_deleted("cand_a")

        # --- passes if not in projection ---
        db_dao.checks_xpansion_candidate_can_be_deleted("cand_b")  # must not raise


class TestXpansionAdequacyCriterion:
    """Tests for Xpansion adequacy criterion CRUD operations."""

    def test_save_and_get_adequacy_criterion(self, db_dao: DatabaseStudyDao) -> None:
        # --- no configuration: returns default ---
        assert db_dao.get_xpansion_adequacy_criterion() == XpansionAdequacyCriterion()

        # --- after create: returns default row values ---
        db_dao.create_xpansion_configuration()
        result = db_dao.get_xpansion_adequacy_criterion()
        defaults = XpansionAdequacyCriterion()
        assert result.stopping_threshold == defaults.stopping_threshold
        assert result.criterion_count_threshold == defaults.criterion_count_threshold
        assert result.patterns == defaults.patterns

        db_dao.save_area("Paris")
        db_dao.save_area("Lyon")

        # --- round-trip with patterns ---
        criterion = XpansionAdequacyCriterion(
            stopping_threshold=500.0,
            criterion_count_threshold=2.5,
            patterns=[
                XpansionAdequacyPattern(area="paris", criterion=0.9),
                XpansionAdequacyPattern(area="lyon", criterion=0.7),
            ],
        )
        db_dao.save_xpansion_adequacy_criterion(criterion)

        result = db_dao.get_xpansion_adequacy_criterion()
        assert result.stopping_threshold == 500.0
        assert result.criterion_count_threshold == 2.5
        assert {p.area: p.criterion for p in result.patterns} == {"paris": 0.9, "lyon": 0.7}

        # --- upsert clears patterns ---
        db_dao.save_xpansion_adequacy_criterion(XpansionAdequacyCriterion(stopping_threshold=999.0, patterns=[]))
        result = db_dao.get_xpansion_adequacy_criterion()
        assert result.stopping_threshold == 999.0
        assert result.patterns == []

        # --- raises for missing area ---
        with pytest.raises(AreaNotFound):
            db_dao.save_xpansion_adequacy_criterion(
                XpansionAdequacyCriterion(patterns=[XpansionAdequacyPattern(area="nonexistent", criterion=0.5)])
            )


class TestCascadeDelete:
    """Tests for cascade-delete behaviour when the Xpansion configuration is removed."""

    def test_cascade_delete_removes_all_related_rows(self, db_session: Session, db_dao: DatabaseStudyDao) -> None:
        """Deleting the configuration should cascade-delete candidates, projection, criterion and patterns."""
        # --- setup ---
        db_dao.create_xpansion_configuration()
        db_dao.save_area("Paris")
        db_dao.save_area("Lyon")
        db_dao.save_link(Link(area1="paris", area2="lyon"))
        db_dao.save_xpansion_candidate(_make_candidate("cand", "lyon", "paris"))
        db_dao.save_xpansion_settings(
            XpansionSettings(sensitivity_config=XpansionSensitivitySettings(projection=["cand"]))
        )
        db_dao.save_xpansion_adequacy_criterion(
            XpansionAdequacyCriterion(patterns=[XpansionAdequacyPattern(area="paris", criterion=1.0)])
        )

        # --- delete ---
        db_dao.delete_xpansion_configuration()

        # --- assert all rows gone ---
        with db_session:
            _assert_tables_empty(
                db_session,
                [
                    XPANSION_SETTINGS_TABLE,
                    XPANSION_CANDIDATE_TABLE,
                    XPANSION_SENSITIVITY_PROJECTION_TABLE,
                    XPANSION_ADEQUACY_CRITERION_TABLE,
                    XPANSION_ADEQUACY_PATTERN_TABLE,
                ],
                db_dao.get_study_id(),
            )

    def test_recreate_configuration_after_delete(self, db_dao: DatabaseStudyDao) -> None:
        """After deleting a configuration, creating it again should succeed with fresh defaults."""
        # --- setup ---
        db_dao.create_xpansion_configuration()
        db_dao.save_xpansion_settings(XpansionSettings(optimality_gap=42.0))

        # --- delete and recreate ---
        db_dao.delete_xpansion_configuration()
        db_dao.create_xpansion_configuration()

        result = db_dao.get_xpansion_settings()
        assert result.optimality_gap == XpansionSettings().optimality_gap


class TestXpansionStudyIsolation:
    """Tests that rows from one study do not leak into another study sharing the same DB."""

    def test_candidates_are_isolated_between_studies(
        self, db_session: Session, matrix_service: ISimpleMatrixService
    ) -> None:
        """Candidates saved in study A must not appear in study B."""
        dao_a = build_db_dao(db_session, matrix_service, STUDY_VERSION_8_8)
        dao_b = build_db_dao(db_session, matrix_service, STUDY_VERSION_8_8)

        dao_a.create_xpansion_configuration()
        dao_b.create_xpansion_configuration()

        dao_a.save_area("x")
        dao_a.save_area("y")
        dao_a.save_link(Link(area1="x", area2="y"))
        dao_a.save_xpansion_candidate(_make_candidate("cand_a", "x", "y"))

        assert len(dao_a.get_all_xpansion_candidates()) == 1
        assert dao_b.get_all_xpansion_candidates() == []

    def test_settings_are_isolated_between_studies(
        self, db_session: Session, matrix_service: ISimpleMatrixService
    ) -> None:
        """Settings saved in study A must not affect study B."""
        dao_a = build_db_dao(db_session, matrix_service, STUDY_VERSION_8_8)
        dao_b = build_db_dao(db_session, matrix_service, STUDY_VERSION_8_8)

        dao_a.create_xpansion_configuration()
        dao_b.create_xpansion_configuration()

        dao_a.save_xpansion_settings(XpansionSettings(optimality_gap=999.0))

        assert dao_b.get_xpansion_settings().optimality_gap == XpansionSettings().optimality_gap
