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

import polars as pl
import pytest
from sqlalchemy import Table, select
from sqlalchemy.orm import Session

from antarest.core.exceptions import (
    AreaNotFound,
    CandidateNotFoundError,
    FileCurrentlyUsedInSettings,
    LinkNotFound,
    XpansionCandidateDeletionError,
    XpansionConfigurationAlreadyExists,
    XpansionConfigurationDoesNotExist,
    XpansionFileNotFoundError,
)
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.link_model import Link
from antarest.study.business.model.xpansion_model import (
    XpansionAdequacyCriterion,
    XpansionAdequacyPattern,
    XpansionCandidate,
    XpansionResourceFileType,
    XpansionSensitivitySettings,
    XpansionSettings,
    XpansionSettingsUpdate,
)
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.dao.database.models.xpansion import (
    XPANSION_ADEQUACY_CRITERION_TABLE,
    XPANSION_ADEQUACY_PATTERN_TABLE,
    XPANSION_CANDIDATE_TABLE,
    XPANSION_CAPACITY_TABLE,
    XPANSION_CONSTRAINT_TABLE,
    XPANSION_SENSITIVITY_PROJECTION_TABLE,
    XPANSION_SETTINGS_TABLE,
    XPANSION_WEIGHT_TABLE,
)


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
        db_dao.save_links([Link(area1="paris", area2="lyon")])
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
        db_dao.save_links([Link(area1="x", area2="y")])
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
        assert sorted(result.sensitivity_config.projection) == ["cand_a", "cand_b"]

        # --- upsert ---
        db_dao.save_xpansion_settings(XpansionSettings(optimality_gap=10.0))
        result = db_dao.get_xpansion_settings()
        assert result.optimality_gap == 10.0

        # --- invalid projection ---
        settings = XpansionSettings(sensitivity_config=XpansionSensitivitySettings(projection=["cand_a", "ghost_cand"]))
        with pytest.raises(CandidateNotFoundError):
            db_dao.save_xpansion_settings(settings)

    def test_checks_xpansion_settings_correct(
        self, db_dao_930_and_matrix_service: tuple[DatabaseStudyDao, ISimpleMatrixService]
    ) -> None:
        """checks_xpansion_settings_are_correct should validate that referenced constraint/weight files exist."""
        db_dao, matrix_service = db_dao_930_and_matrix_service
        db_dao.create_xpansion_configuration()

        # --- missing constraint file raises ---
        with pytest.raises(XpansionFileNotFoundError, match="constraints"):
            db_dao.checks_xpansion_settings_are_correct(
                XpansionSettingsUpdate(additional_constraints="missing_constraints.txt")
            )

        # --- missing weight file raises ---
        with pytest.raises(XpansionFileNotFoundError, match="weights"):
            db_dao.checks_xpansion_settings_are_correct(XpansionSettingsUpdate(yearly_weights="missing_weights.csv"))

        # --- files exist: no raise ---
        series_id = matrix_service.create(pl.DataFrame({"col": [1.0]}))
        db_dao.save_xpansion_weight("weights.csv", series_id)
        db_dao.save_xpansion_constraint("constraints.txt", b"some content")
        db_dao.checks_xpansion_settings_are_correct(
            XpansionSettingsUpdate(additional_constraints="constraints.txt", yearly_weights="weights.csv")
        )  # must not raise

        # --- None fields skip validation ---
        db_dao.checks_xpansion_settings_are_correct(
            XpansionSettingsUpdate(additional_constraints=None, yearly_weights=None)
        )  # must not raise


class TestXpansionCandidates:
    """Tests for Xpansion candidate CRUD operations."""

    def test_candidate_lifecycle(self, db_dao: DatabaseStudyDao) -> None:
        """Full candidate lifecycle: coherence checks, CRUD, upsert, rename (all cases), projection, delete."""
        db_dao.create_xpansion_configuration()
        db_dao.save_area("Paris")
        db_dao.save_area("Lyon")
        db_dao.save_area("Bordeaux")
        db_dao.save_links([Link(area1="paris", area2="lyon"), Link(area1="bordeaux", area2="paris")])

        # --- coherence: missing area / link raises, valid passes ---
        with pytest.raises(AreaNotFound):
            db_dao.checks_xpansion_candidate_coherence(_make_candidate("c", "nowhere", "paris"))
        with pytest.raises(LinkNotFound):
            db_dao.checks_xpansion_candidate_coherence(_make_candidate("c", "bordeaux", "lyon"))
        db_dao.checks_xpansion_candidate_coherence(_make_candidate("c", "lyon", "paris"))  # no raise

        # --- initially empty ---
        assert db_dao.get_all_xpansion_candidates() == []

        # --- save / get / get_all ---
        db_dao.save_xpansion_candidate(_make_candidate("alice", "lyon", "paris", cost=1000.0))
        db_dao.save_xpansion_candidate(_make_candidate("bob", "bordeaux", "paris", cost=2000.0))
        result = db_dao.get_xpansion_candidate("alice")
        assert result.annual_cost_per_mw == 1000.0
        assert result.link.area_from == "lyon"
        assert {c.name for c in db_dao.get_all_xpansion_candidates()} == {"alice", "bob"}

        with pytest.raises(CandidateNotFoundError):
            db_dao.get_xpansion_candidate("nonexistent")

        # --- upsert (no old_id) ---
        db_dao.save_xpansion_candidate(_make_candidate("alice", "lyon", "paris", cost=9999.0))
        assert db_dao.get_xpansion_candidate("alice").annual_cost_per_mw == 9999.0
        assert len(db_dao.get_all_xpansion_candidates()) == 2

        # --- old_id == name is a plain upsert ---
        db_dao.save_xpansion_candidate(_make_candidate("alice", "lyon", "paris", cost=500.0), old_id="alice")
        assert db_dao.get_xpansion_candidate("alice").annual_cost_per_mw == 500.0
        assert len(db_dao.get_all_xpansion_candidates()) == 2

        # --- set up projection for rename tests ---
        db_dao.save_xpansion_settings(
            XpansionSettings(sensitivity_config=XpansionSensitivitySettings(projection=["alice", "bob"]))
        )

        # --- nonexistent old_id raises, original candidate untouched ---
        with pytest.raises(CandidateNotFoundError):
            db_dao.save_xpansion_candidate(_make_candidate("alice", "lyon", "paris"), old_id="ghost")

        # --- basic rename: old row gone, new row present, projection carried over ---
        db_dao.save_xpansion_candidate(_make_candidate("charlie", "lyon", "paris", cost=500.0), old_id="alice")
        with pytest.raises(CandidateNotFoundError):
            db_dao.get_xpansion_candidate("alice")
        assert db_dao.get_xpansion_candidate("charlie").annual_cost_per_mw == 500.0
        proj = db_dao.get_xpansion_settings().sensitivity_config.projection
        assert "charlie" in proj and "alice" not in proj

        # --- rename to existing target overwrites it; no duplicate in projection ---
        db_dao.save_xpansion_candidate(_make_candidate("bob", "bordeaux", "paris", cost=999.0), old_id="charlie")
        assert len(db_dao.get_all_xpansion_candidates()) == 1
        assert db_dao.get_xpansion_candidate("bob").annual_cost_per_mw == 999.0
        proj = db_dao.get_xpansion_settings().sensitivity_config.projection
        assert proj == ["bob"]

        # --- checks_candidate_can_be_deleted ---
        with pytest.raises(XpansionCandidateDeletionError):
            db_dao.checks_xpansion_candidate_can_be_deleted("bob")
        db_dao.checks_xpansion_candidate_can_be_deleted("nobody")  # no raise

        # --- removing bob from projection unblocks deletion ---
        db_dao.save_xpansion_settings(XpansionSettings(sensitivity_config=XpansionSensitivitySettings(projection=[])))
        db_dao.checks_xpansion_candidate_can_be_deleted("bob")  # no raise

        # --- delete ---
        db_dao.delete_xpansion_candidate("bob")
        assert db_dao.get_all_xpansion_candidates() == []
        with pytest.raises(CandidateNotFoundError):
            db_dao.delete_xpansion_candidate("bob")

    @pytest.mark.parametrize(
        "profile_field",
        [
            "link_profile",
            "already_installed_link_profile",
            "direct_link_profile",
            "indirect_link_profile",
            "already_installed_direct_link_profile",
            "already_installed_indirect_link_profile",
        ],
    )
    def test_candidate_coherence_raises_for_missing_capacity_profile(
        self, db_dao_930_and_matrix_service: tuple[DatabaseStudyDao, ISimpleMatrixService], profile_field: str
    ) -> None:
        """checks_xpansion_candidate_coherence should raise when a link profile references a non-existent capacity."""
        db_dao, matrix_service = db_dao_930_and_matrix_service
        db_dao.create_xpansion_configuration()
        db_dao.save_area("Paris")
        db_dao.save_area("Lyon")
        db_dao.save_links([Link(area1="paris", area2="lyon")])

        candidate = XpansionCandidate(
            name="cand",
            link="lyon - paris",
            annual_cost_per_mw=100.0,
            max_investment=1000.0,
            **{profile_field: "missing_capa.txt"},
        )

        # --- profile file absent: raises ---
        with pytest.raises(XpansionFileNotFoundError, match="missing_capa.txt"):
            db_dao.checks_xpansion_candidate_coherence(candidate)

        # --- profile file present: no raise ---
        series_id = matrix_service.create(pl.DataFrame({"col": [1.0]}))
        db_dao.save_xpansion_capacity("missing_capa.txt", series_id)
        db_dao.checks_xpansion_candidate_coherence(candidate)  # must not raise


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
        db_dao.save_links([Link(area1="paris", area2="lyon")])
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

    def test_deleting_link_cascades_to_candidates(self, db_dao: DatabaseStudyDao) -> None:
        """Deleting a link should cascade-delete all candidates referencing it."""
        db_dao.create_xpansion_configuration()
        db_dao.save_area("Paris")
        db_dao.save_area("Lyon")
        db_dao.save_links([Link(area1="paris", area2="lyon")])
        db_dao.save_xpansion_candidate(_make_candidate("cand1", "lyon", "paris"))
        db_dao.save_xpansion_candidate(_make_candidate("cand2", "lyon", "paris"))

        db_dao.delete_link(Link(area1="paris", area2="lyon"))

        assert db_dao.get_all_xpansion_candidates() == []

    def test_cascade_delete_removes_resource_rows(
        self, db_session: Session, db_dao_930_and_matrix_service: tuple[DatabaseStudyDao, ISimpleMatrixService]
    ) -> None:
        """Deleting the configuration should cascade-delete constraint, capacity and weight rows."""
        db_dao, matrix_service = db_dao_930_and_matrix_service
        db_dao.create_xpansion_configuration()
        series_id = matrix_service.create(pl.DataFrame({"col": [1.0]}))
        db_dao.save_xpansion_constraint("my.txt", b"content")
        db_dao.save_xpansion_capacity("capa.txt", series_id)
        db_dao.save_xpansion_weight("weights.csv", series_id)

        db_dao.delete_xpansion_configuration()

        with db_session:
            _assert_tables_empty(
                db_session,
                [XPANSION_CONSTRAINT_TABLE, XPANSION_CAPACITY_TABLE, XPANSION_WEIGHT_TABLE],
                db_dao.get_study_id(),
            )


class TestXpansionResources:
    """Tests for Xpansion resource CRUD: constraints (bytes), capacities and weights (DataFrame)."""

    def test_constraint_save_get_list_delete(self, db_dao: DatabaseStudyDao) -> None:
        """Constraint: round-trip save/get, listing, upsert, not-found, and delete."""
        db_dao.create_xpansion_configuration()

        # --- initially empty ---
        assert db_dao.get_xpansion_resources(XpansionResourceFileType.CONSTRAINTS) == []

        # --- save and get ---
        db_dao.save_xpansion_constraint("my_constraints.txt", b"line1\nline2")
        result = db_dao.get_xpansion_resource(XpansionResourceFileType.CONSTRAINTS, "my_constraints.txt")
        assert result == b"line1\nline2"

        # --- listing (sorted) ---
        db_dao.save_xpansion_constraint("zzz.txt", b"z")
        db_dao.save_xpansion_constraint("aaa.txt", b"a")
        assert db_dao.get_xpansion_resources(XpansionResourceFileType.CONSTRAINTS) == [
            "aaa.txt",
            "my_constraints.txt",
            "zzz.txt",
        ]

        # --- upsert ---
        db_dao.save_xpansion_constraint("my_constraints.txt", b"updated")
        result = db_dao.get_xpansion_resource(XpansionResourceFileType.CONSTRAINTS, "my_constraints.txt")
        assert result == b"updated"

        # --- get not found ---
        with pytest.raises(XpansionFileNotFoundError):
            db_dao.get_xpansion_resource(XpansionResourceFileType.CONSTRAINTS, "nonexistent.txt")

        # --- delete ---
        db_dao.delete_xpansion_resource(XpansionResourceFileType.CONSTRAINTS, "my_constraints.txt")
        assert "my_constraints.txt" not in db_dao.get_xpansion_resources(XpansionResourceFileType.CONSTRAINTS)

        # --- delete not found ---
        with pytest.raises(XpansionFileNotFoundError):
            db_dao.delete_xpansion_resource(XpansionResourceFileType.CONSTRAINTS, "my_constraints.txt")

    def test_capacity_save_get_list_delete(
        self, db_dao_930_and_matrix_service: tuple[DatabaseStudyDao, ISimpleMatrixService]
    ) -> None:
        """Capacity: round-trip save/get (DataFrame), listing, upsert, not-found, and delete."""
        db_dao, matrix_service = db_dao_930_and_matrix_service
        db_dao.create_xpansion_configuration()

        # --- initially empty ---
        assert db_dao.get_xpansion_resources(XpansionResourceFileType.CAPACITIES) == []

        # --- save and get ---
        df = pl.DataFrame({"col1": [1.0, 2.0], "col2": [3.0, 4.0]})
        series_id = matrix_service.create(df)
        db_dao.save_xpansion_capacity("link_capa.txt", series_id)

        result = db_dao.get_xpansion_resource(XpansionResourceFileType.CAPACITIES, "link_capa.txt")
        assert isinstance(result, pl.DataFrame)
        assert result.equals(df)

        # --- listing (sorted) ---
        db_dao.save_xpansion_capacity("zzz.txt", series_id)
        db_dao.save_xpansion_capacity("aaa.txt", series_id)
        assert db_dao.get_xpansion_resources(XpansionResourceFileType.CAPACITIES) == [
            "aaa.txt",
            "link_capa.txt",
            "zzz.txt",
        ]

        # --- upsert with different series ---
        df2 = pl.DataFrame({"col1": [9.0]})
        series_id2 = matrix_service.create(df2)
        db_dao.save_xpansion_capacity("link_capa.txt", series_id2)
        result = db_dao.get_xpansion_resource(XpansionResourceFileType.CAPACITIES, "link_capa.txt")
        assert isinstance(result, pl.DataFrame)
        assert result.equals(df2)

        # --- get not found ---
        with pytest.raises(XpansionFileNotFoundError):
            db_dao.get_xpansion_resource(XpansionResourceFileType.CAPACITIES, "nonexistent.txt")

        # --- delete ---
        db_dao.delete_xpansion_resource(XpansionResourceFileType.CAPACITIES, "link_capa.txt")
        assert "link_capa.txt" not in db_dao.get_xpansion_resources(XpansionResourceFileType.CAPACITIES)

        # --- delete not found ---
        with pytest.raises(XpansionFileNotFoundError):
            db_dao.delete_xpansion_resource(XpansionResourceFileType.CAPACITIES, "link_capa.txt")

    def test_weight_save_get_list_delete(
        self, db_dao_930_and_matrix_service: tuple[DatabaseStudyDao, ISimpleMatrixService]
    ) -> None:
        """Weight: round-trip save/get (DataFrame), listing, upsert, not-found, and delete."""
        db_dao, matrix_service = db_dao_930_and_matrix_service
        db_dao.create_xpansion_configuration()

        # --- save and get ---
        df = pl.DataFrame({"w": [0.5, 0.3, 0.2]})
        series_id = matrix_service.create(df)
        db_dao.save_xpansion_weight("mc_weights.csv", series_id)

        result = db_dao.get_xpansion_resource(XpansionResourceFileType.WEIGHTS, "mc_weights.csv")
        assert isinstance(result, pl.DataFrame)
        assert result.equals(df)

        # --- listing (sorted) ---
        db_dao.save_xpansion_weight("zzz.csv", series_id)
        db_dao.save_xpansion_weight("aaa.csv", series_id)
        assert db_dao.get_xpansion_resources(XpansionResourceFileType.WEIGHTS) == [
            "aaa.csv",
            "mc_weights.csv",
            "zzz.csv",
        ]

        # --- upsert with different series ---
        df2 = pl.DataFrame({"w": [0.9]})
        series_id2 = matrix_service.create(df2)
        db_dao.save_xpansion_weight("mc_weights.csv", series_id2)
        result = db_dao.get_xpansion_resource(XpansionResourceFileType.WEIGHTS, "mc_weights.csv")
        assert isinstance(result, pl.DataFrame)
        assert result.equals(df2)

        # --- get not found ---
        with pytest.raises(XpansionFileNotFoundError):
            db_dao.get_xpansion_resource(XpansionResourceFileType.WEIGHTS, "nonexistent.csv")

        # --- delete ---
        db_dao.delete_xpansion_resource(XpansionResourceFileType.WEIGHTS, "mc_weights.csv")
        assert "mc_weights.csv" not in db_dao.get_xpansion_resources(XpansionResourceFileType.WEIGHTS)

        # --- delete not found ---
        with pytest.raises(XpansionFileNotFoundError):
            db_dao.delete_xpansion_resource(XpansionResourceFileType.WEIGHTS, "mc_weights.csv")

    def test_checks_constraint_can_be_deleted_raises_if_used_in_settings(self, db_dao: DatabaseStudyDao) -> None:
        """checks_xpansion_resource_can_be_deleted should raise if constraint file is referenced by settings."""
        db_dao.create_xpansion_configuration()
        db_dao.save_xpansion_constraint("my.txt", b"data")
        db_dao.save_xpansion_settings(XpansionSettings(additional_constraints="my.txt"))

        with pytest.raises(FileCurrentlyUsedInSettings):
            db_dao.checks_xpansion_resource_can_be_deleted(XpansionResourceFileType.CONSTRAINTS, "my.txt")

        db_dao.save_xpansion_constraint("other.txt", b"x")
        db_dao.checks_xpansion_resource_can_be_deleted(XpansionResourceFileType.CONSTRAINTS, "other.txt")  # no raise

    def test_checks_weight_can_be_deleted_raises_if_used_in_settings(self, db_dao: DatabaseStudyDao) -> None:
        """checks_xpansion_resource_can_be_deleted should raise if weight file is referenced by settings."""
        db_dao.create_xpansion_configuration()
        db_dao.save_xpansion_settings(XpansionSettings(yearly_weights="mc.csv"))

        with pytest.raises(FileCurrentlyUsedInSettings):
            db_dao.checks_xpansion_resource_can_be_deleted(XpansionResourceFileType.WEIGHTS, "mc.csv")

        db_dao.checks_xpansion_resource_can_be_deleted(XpansionResourceFileType.WEIGHTS, "unused.csv")  # no raise

    @pytest.mark.parametrize(
        "profile_field",
        [
            "link_profile",
            "already_installed_link_profile",
            "direct_link_profile",
            "indirect_link_profile",
            "already_installed_direct_link_profile",
            "already_installed_indirect_link_profile",
        ],
    )
    def test_checks_capacity_can_be_deleted_raises_if_used_by_candidate(
        self, db_dao: DatabaseStudyDao, profile_field: str
    ) -> None:
        """checks_xpansion_resource_can_be_deleted should raise for any of the 6 candidate profile columns."""
        db_dao.create_xpansion_configuration()
        db_dao.save_area("Paris")
        db_dao.save_area("Lyon")
        db_dao.save_links([Link(area1="paris", area2="lyon")])

        candidate = XpansionCandidate(
            name="cand",
            link="lyon - paris",
            annual_cost_per_mw=100.0,
            max_investment=1000.0,
            **{profile_field: "used_capa.txt"},
        )
        db_dao.save_xpansion_candidate(candidate)

        with pytest.raises(FileCurrentlyUsedInSettings):
            db_dao.checks_xpansion_resource_can_be_deleted(XpansionResourceFileType.CAPACITIES, "used_capa.txt")

        db_dao.checks_xpansion_resource_can_be_deleted(XpansionResourceFileType.CAPACITIES, "other.txt")  # no raise
