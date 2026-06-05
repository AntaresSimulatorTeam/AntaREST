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
from antarest.study.dao.api.study_dao import StudyDao
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
from tests.study.dao.utils import save_area


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
        save_area(db_dao, "Paris")
        save_area(db_dao, "Lyon")
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

    def test_get_xpansion_settings_returns_defaults_after_create(self, dao: StudyDao) -> None:
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

    def test_get_xpansion_settings_raises_if_no_configuration(self, dao: StudyDao) -> None:
        """get_xpansion_settings should raise when no configuration exists."""
        with pytest.raises(XpansionConfigurationDoesNotExist):
            dao.get_xpansion_settings()

    def test_save_xpansion_settings_persists_non_default_values(self, dao: StudyDao) -> None:
        """save_xpansion_settings should persist all non-default values and allow retrieval."""
        # --- setup ---
        dao.create_xpansion_configuration()
        save_area(dao, "x")
        save_area(dao, "y")
        dao.save_links([Link(area1="x", area2="y")])
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
        assert sorted(result.sensitivity_config.projection) == ["cand_a", "cand_b"]

        # --- upsert ---
        dao.save_xpansion_settings(XpansionSettings(optimality_gap=10.0))
        result = dao.get_xpansion_settings()
        assert result.optimality_gap == 10.0

        # --- invalid projection: validate candidates exist ---
        settings = XpansionSettings(sensitivity_config=XpansionSensitivitySettings(projection=["cand_a", "ghost_cand"]))
        with pytest.raises(CandidateNotFoundError):
            dao.save_xpansion_settings(settings)

    def test_checks_xpansion_settings_correct(
        self, dao_and_matrix_service: tuple[StudyDao, ISimpleMatrixService]
    ) -> None:
        """checks_xpansion_settings_are_correct should validate that referenced constraint/weight files exist."""
        dao, matrix_service = dao_and_matrix_service
        dao.create_xpansion_configuration()

        # --- missing constraint file raises ---
        with pytest.raises(XpansionFileNotFoundError, match="constraints"):
            dao.checks_xpansion_settings_are_correct(
                XpansionSettingsUpdate(additional_constraints="missing_constraints.txt")
            )

        # --- missing weight file raises ---
        with pytest.raises(XpansionFileNotFoundError, match="weights"):
            dao.checks_xpansion_settings_are_correct(XpansionSettingsUpdate(yearly_weights="missing_weights.csv"))

        # --- files exist: no raise ---
        series_id = matrix_service.create(pl.DataFrame({"col": [1.0]}))
        dao.save_xpansion_weight({"weights.csv": series_id})
        dao.save_xpansion_constraint({"constraints.txt": b"some content"})
        dao.checks_xpansion_settings_are_correct(
            XpansionSettingsUpdate(additional_constraints="constraints.txt", yearly_weights="weights.csv")
        )  # must not raise

        # --- None fields skip validation ---
        dao.checks_xpansion_settings_are_correct(
            XpansionSettingsUpdate(additional_constraints=None, yearly_weights=None)
        )  # must not raise


class TestXpansionCandidates:
    """Tests for Xpansion candidate CRUD operations."""

    def test_candidate_lifecycle(self, dao: StudyDao) -> None:
        """Full candidate lifecycle: coherence checks, CRUD, upsert, rename (all cases), projection, delete."""
        dao.create_xpansion_configuration()
        save_area(dao, "Paris")
        save_area(dao, "Lyon")
        save_area(dao, "Bordeaux")
        dao.save_links([Link(area1="paris", area2="lyon"), Link(area1="bordeaux", area2="paris")])

        # --- coherence: missing area / link raises, valid passes ---
        with pytest.raises(AreaNotFound):
            dao.checks_xpansion_candidate_coherence(_make_candidate("c", "nowhere", "paris"))
        with pytest.raises(LinkNotFound):
            dao.checks_xpansion_candidate_coherence(_make_candidate("c", "bordeaux", "lyon"))
        dao.checks_xpansion_candidate_coherence(_make_candidate("c", "lyon", "paris"))  # no raise

        # --- initially empty ---
        assert dao.get_all_xpansion_candidates() == []

        # --- save / get / get_all ---
        dao.save_xpansion_candidate(_make_candidate("alice", "lyon", "paris", cost=1000.0))
        dao.save_xpansion_candidate(_make_candidate("bob", "bordeaux", "paris", cost=2000.0))
        result = dao.get_xpansion_candidate("alice")
        assert result.annual_cost_per_mw == 1000.0
        assert result.link.area_from == "lyon"
        assert {c.name for c in dao.get_all_xpansion_candidates()} == {"alice", "bob"}

        with pytest.raises(CandidateNotFoundError):
            dao.get_xpansion_candidate("nonexistent")

        # --- upsert (no old_id) ---
        dao.save_xpansion_candidate(_make_candidate("alice", "lyon", "paris", cost=9999.0))
        assert dao.get_xpansion_candidate("alice").annual_cost_per_mw == 9999.0
        assert len(dao.get_all_xpansion_candidates()) == 2

        # --- old_id == name is a plain upsert ---
        dao.save_xpansion_candidate(_make_candidate("alice", "lyon", "paris", cost=500.0), old_id="alice")
        assert dao.get_xpansion_candidate("alice").annual_cost_per_mw == 500.0
        assert len(dao.get_all_xpansion_candidates()) == 2

        # --- set up projection for rename tests ---
        dao.save_xpansion_settings(
            XpansionSettings(sensitivity_config=XpansionSensitivitySettings(projection=["alice", "bob"]))
        )

        # --- nonexistent old_id raises, original candidate untouched ---
        with pytest.raises(CandidateNotFoundError):
            dao.save_xpansion_candidate(_make_candidate("alice", "lyon", "paris"), old_id="ghost")

        # --- basic rename: old row gone, new row present ---
        dao.save_xpansion_candidate(_make_candidate("charlie", "lyon", "paris", cost=500.0), old_id="alice")
        with pytest.raises(CandidateNotFoundError):
            dao.get_xpansion_candidate("alice")
        assert dao.get_xpansion_candidate("charlie").annual_cost_per_mw == 500.0
        # Rename carries over to the projection (DB via cascade, FS via explicit rewrite)
        proj = dao.get_xpansion_settings().sensitivity_config.projection
        assert "charlie" in proj and "alice" not in proj

        dao.save_xpansion_candidate(_make_candidate("bob", "bordeaux", "paris", cost=999.0), old_id="charlie")
        assert len(dao.get_all_xpansion_candidates()) == 1
        assert dao.get_xpansion_candidate("bob").annual_cost_per_mw == 999.0
        assert dao.get_xpansion_settings().sensitivity_config.projection == ["bob"]

        # --- checks_candidate_can_be_deleted ---
        with pytest.raises(XpansionCandidateDeletionError):
            dao.checks_xpansion_candidate_can_be_deleted("bob")
        dao.checks_xpansion_candidate_can_be_deleted("nobody")  # no raise

        # --- removing bob from projection unblocks deletion ---
        dao.save_xpansion_settings(XpansionSettings(sensitivity_config=XpansionSensitivitySettings(projection=[])))
        dao.checks_xpansion_candidate_can_be_deleted("bob")  # no raise

        # --- delete ---
        dao.delete_xpansion_candidate("bob")
        assert dao.get_all_xpansion_candidates() == []
        with pytest.raises(CandidateNotFoundError):
            dao.delete_xpansion_candidate("bob")

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
        self, dao_and_matrix_service: tuple[StudyDao, ISimpleMatrixService], profile_field: str
    ) -> None:
        """checks_xpansion_candidate_coherence should raise when a link profile references a non-existent capacity."""
        dao, matrix_service = dao_and_matrix_service
        dao.create_xpansion_configuration()
        save_area(dao, "Paris")
        save_area(dao, "Lyon")
        dao.save_links([Link(area1="paris", area2="lyon")])

        candidate = XpansionCandidate(
            name="cand",
            link="lyon - paris",
            annual_cost_per_mw=100.0,
            max_investment=1000.0,
            **{profile_field: "missing_capa.txt"},
        )

        # --- profile file absent: raises ---
        with pytest.raises(XpansionFileNotFoundError, match="missing_capa.txt"):
            dao.checks_xpansion_candidate_coherence(candidate)

        # --- profile file present: no raise ---
        series_id = matrix_service.create(pl.DataFrame({"col": [1.0]}))
        dao.save_xpansion_capacity({"missing_capa.txt": series_id})
        dao.checks_xpansion_candidate_coherence(candidate)  # must not raise


class TestXpansionAdequacyCriterion:
    """Tests for Xpansion adequacy criterion CRUD operations."""

    def test_save_and_get_adequacy_criterion(self, dao: StudyDao) -> None:
        # --- no configuration: returns default ---
        assert dao.get_xpansion_adequacy_criterion() == XpansionAdequacyCriterion()

        # --- after create: returns default row values ---
        dao.create_xpansion_configuration()
        result = dao.get_xpansion_adequacy_criterion()
        defaults = XpansionAdequacyCriterion()
        assert result.stopping_threshold == defaults.stopping_threshold
        assert result.criterion_count_threshold == defaults.criterion_count_threshold
        assert result.patterns == defaults.patterns

        save_area(dao, "Paris")
        save_area(dao, "Lyon")

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

    def test_cascade_delete_removes_all_related_rows(self, db_session: Session, db_dao: DatabaseStudyDao) -> None:
        """Deleting the configuration should cascade-delete candidates, projection, criterion and patterns."""
        # --- setup ---
        db_dao.create_xpansion_configuration()
        save_area(db_dao, "Paris")
        save_area(db_dao, "Lyon")
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

    def test_recreate_configuration_after_delete(self, dao: StudyDao) -> None:
        """After deleting a configuration, creating it again should succeed with fresh defaults."""
        # --- setup ---
        dao.create_xpansion_configuration()
        dao.save_xpansion_settings(XpansionSettings(optimality_gap=42.0))

        # --- delete and recreate ---
        dao.delete_xpansion_configuration()
        dao.create_xpansion_configuration()

        result = dao.get_xpansion_settings()
        assert result.optimality_gap == XpansionSettings().optimality_gap

    def test_deleting_link_cascades_to_candidates(self, dao: StudyDao) -> None:
        """Deleting a link should cascade-delete all candidates referencing it.
        DB enforces this via FK cascade; FS does not. Intentional permanent divergence:
        FS will not get a cascade implementation."""
        dao.create_xpansion_configuration()
        save_area(dao, "Paris")
        save_area(dao, "Lyon")
        dao.save_links([Link(area1="paris", area2="lyon")])
        dao.save_xpansion_candidate(_make_candidate("cand1", "lyon", "paris"))
        dao.save_xpansion_candidate(_make_candidate("cand2", "lyon", "paris"))

        dao.delete_link(Link(area1="paris", area2="lyon"))

        if isinstance(dao, DatabaseStudyDao):
            assert dao.get_all_xpansion_candidates() == []
        else:
            # FS backend does not cascade-delete candidates when a link is removed.
            assert len(dao.get_all_xpansion_candidates()) == 2

    def test_cascade_delete_removes_resource_rows(
        self, db_session: Session, db_dao_930_and_matrix_service: tuple[DatabaseStudyDao, ISimpleMatrixService]
    ) -> None:
        """Deleting the configuration should cascade-delete constraint, capacity and weight rows."""
        db_dao, matrix_service = db_dao_930_and_matrix_service
        db_dao.create_xpansion_configuration()
        series_id = matrix_service.create(pl.DataFrame({"col": [1.0]}))
        db_dao.save_xpansion_constraint({"my.txt": b"content"})
        db_dao.save_xpansion_capacity({"capa.txt": series_id})
        db_dao.save_xpansion_weight({"weights.csv": series_id})

        db_dao.delete_xpansion_configuration()

        with db_session:
            _assert_tables_empty(
                db_session,
                [XPANSION_CONSTRAINT_TABLE, XPANSION_CAPACITY_TABLE, XPANSION_WEIGHT_TABLE],
                db_dao.get_study_id(),
            )


class TestXpansionResources:
    """Tests for Xpansion resource CRUD: constraints (bytes), capacities and weights (DataFrame)."""

    def test_constraint_save_get_list_delete(self, dao: StudyDao) -> None:
        """Constraint: round-trip save/get, listing, upsert, not-found, and delete."""
        dao.create_xpansion_configuration()

        # --- initially empty ---
        assert dao.get_xpansion_resources(XpansionResourceFileType.CONSTRAINTS) == []

        # --- save and get ---
        dao.save_xpansion_constraint({"my_constraints.txt": b"line1\nline2"})
        result = dao.get_xpansion_resource(XpansionResourceFileType.CONSTRAINTS, "my_constraints.txt")
        assert result == b"line1\nline2"

        # --- listing (sorted) ---
        dao.save_xpansion_constraint({"zzz.txt": b"z", "aaa.txt": b"a"})
        assert dao.get_xpansion_resources(XpansionResourceFileType.CONSTRAINTS) == [
            "aaa.txt",
            "my_constraints.txt",
            "zzz.txt",
        ]

        # --- upsert ---
        dao.save_xpansion_constraint({"my_constraints.txt": b"updated"})
        result = dao.get_xpansion_resource(XpansionResourceFileType.CONSTRAINTS, "my_constraints.txt")
        assert result == b"updated"

        # --- get not found ---
        with pytest.raises(XpansionFileNotFoundError):
            dao.get_xpansion_resource(XpansionResourceFileType.CONSTRAINTS, "nonexistent.txt")

        # --- delete ---
        dao.delete_xpansion_resource(XpansionResourceFileType.CONSTRAINTS, "my_constraints.txt")
        assert "my_constraints.txt" not in dao.get_xpansion_resources(XpansionResourceFileType.CONSTRAINTS)

        # --- delete not found ---
        with pytest.raises(XpansionFileNotFoundError):
            dao.delete_xpansion_resource(XpansionResourceFileType.CONSTRAINTS, "my_constraints.txt")

    def test_capacity_save_get_list_delete(self, dao_and_matrix_service: tuple[StudyDao, ISimpleMatrixService]) -> None:
        """Capacity: round-trip save/get (DataFrame), listing, upsert, not-found, and delete."""
        dao, matrix_service = dao_and_matrix_service
        dao.create_xpansion_configuration()

        # --- initially empty ---
        assert dao.get_xpansion_resources(XpansionResourceFileType.CAPACITIES) == []

        # --- save and get ---
        df = pl.DataFrame({"col1": [1.0, 2.0], "col2": [3.0, 4.0]})
        series_id = matrix_service.create(df)
        dao.save_xpansion_capacity({"link_capa.txt": series_id})

        result = dao.get_xpansion_resource(XpansionResourceFileType.CAPACITIES, "link_capa.txt")
        assert isinstance(result, pl.DataFrame)
        assert result.equals(df)

        # --- listing (sorted) ---
        dao.save_xpansion_capacity({"zzz.txt": series_id, "aaa.txt": series_id})
        assert dao.get_xpansion_resources(XpansionResourceFileType.CAPACITIES) == [
            "aaa.txt",
            "link_capa.txt",
            "zzz.txt",
        ]

        # --- upsert with different series ---
        df2 = pl.DataFrame({"col1": [9.0]})
        series_id2 = matrix_service.create(df2)
        dao.save_xpansion_capacity({"link_capa.txt": series_id2})
        result = dao.get_xpansion_resource(XpansionResourceFileType.CAPACITIES, "link_capa.txt")
        assert isinstance(result, pl.DataFrame)
        assert result.equals(df2)

        # --- get not found ---
        with pytest.raises(XpansionFileNotFoundError):
            dao.get_xpansion_resource(XpansionResourceFileType.CAPACITIES, "nonexistent.txt")

        # --- delete ---
        dao.delete_xpansion_resource(XpansionResourceFileType.CAPACITIES, "link_capa.txt")
        assert "link_capa.txt" not in dao.get_xpansion_resources(XpansionResourceFileType.CAPACITIES)

        # --- delete not found ---
        with pytest.raises(XpansionFileNotFoundError):
            dao.delete_xpansion_resource(XpansionResourceFileType.CAPACITIES, "link_capa.txt")

    def test_weight_save_get_list_delete(self, dao_and_matrix_service: tuple[StudyDao, ISimpleMatrixService]) -> None:
        """Weight: round-trip save/get (DataFrame), listing, upsert, not-found, and delete."""
        dao, matrix_service = dao_and_matrix_service
        dao.create_xpansion_configuration()

        # --- save and get ---
        df = pl.DataFrame({"w": [0.5, 0.3, 0.2]})
        series_id = matrix_service.create(df)
        dao.save_xpansion_weight({"mc_weights.csv": series_id})

        result = dao.get_xpansion_resource(XpansionResourceFileType.WEIGHTS, "mc_weights.csv")
        assert isinstance(result, pl.DataFrame)
        assert result.equals(df)

        # --- listing (sorted) ---
        dao.save_xpansion_weight({"zzz.csv": series_id, "aaa.csv": series_id})
        assert dao.get_xpansion_resources(XpansionResourceFileType.WEIGHTS) == [
            "aaa.csv",
            "mc_weights.csv",
            "zzz.csv",
        ]

        # --- upsert with different series ---
        df2 = pl.DataFrame({"w": [0.9]})
        series_id2 = matrix_service.create(df2)
        dao.save_xpansion_weight({"mc_weights.csv": series_id2})
        result = dao.get_xpansion_resource(XpansionResourceFileType.WEIGHTS, "mc_weights.csv")
        assert isinstance(result, pl.DataFrame)
        assert result.equals(df2)

        # --- get not found ---
        with pytest.raises(XpansionFileNotFoundError):
            dao.get_xpansion_resource(XpansionResourceFileType.WEIGHTS, "nonexistent.csv")

        # --- delete ---
        dao.delete_xpansion_resource(XpansionResourceFileType.WEIGHTS, "mc_weights.csv")
        assert "mc_weights.csv" not in dao.get_xpansion_resources(XpansionResourceFileType.WEIGHTS)

        # --- delete not found ---
        with pytest.raises(XpansionFileNotFoundError):
            dao.delete_xpansion_resource(XpansionResourceFileType.WEIGHTS, "mc_weights.csv")

    def test_get_all_xpansion_weights_returns_saved_data(
        self, db_dao_930_and_matrix_service: tuple[DatabaseStudyDao, ISimpleMatrixService]
    ) -> None:
        """get_all_xpansion_weights should return {filename: matrix_id} for all saved weights."""
        db_dao, matrix_service = db_dao_930_and_matrix_service
        db_dao.create_xpansion_configuration()

        series_id = matrix_service.create(pl.DataFrame({"col": [1.0, 2.0]}))
        db_dao.save_xpansion_weight({"weights.csv": series_id})

        assert db_dao.get_all_xpansion_weights() == {"weights.csv": series_id}

    def test_get_all_xpansion_capacities_returns_saved_data(
        self, db_dao_930_and_matrix_service: tuple[DatabaseStudyDao, ISimpleMatrixService]
    ) -> None:
        """get_all_xpansion_capacities should return {filename: matrix_id} for all saved capacities."""
        db_dao, matrix_service = db_dao_930_and_matrix_service
        db_dao.create_xpansion_configuration()

        series_id = matrix_service.create(pl.DataFrame({"col": [1.0, 2.0]}))
        db_dao.save_xpansion_capacity({"capa.txt": series_id})

        assert db_dao.get_all_xpansion_capacities() == {"capa.txt": series_id}

    def test_get_all_xpansion_constraints_returns_saved_data(self, db_dao: DatabaseStudyDao) -> None:
        """get_all_xpansion_constraints should return {filename: content-bytes} for all saved constraints."""
        db_dao.create_xpansion_configuration()
        db_dao.save_xpansion_constraint({"constraint.txt": b"content-bytes"})

        assert db_dao.get_all_xpansion_constraints() == {"constraint.txt": b"content-bytes"}

    def test_checks_constraint_can_be_deleted_raises_if_used_in_settings(self, dao: StudyDao) -> None:
        """checks_xpansion_resource_can_be_deleted should raise if constraint file is referenced by settings."""
        dao.create_xpansion_configuration()
        dao.save_xpansion_constraint({"my.txt": b"data"})
        dao.save_xpansion_settings(XpansionSettings(additional_constraints="my.txt"))

        with pytest.raises(FileCurrentlyUsedInSettings):
            dao.checks_xpansion_resource_can_be_deleted(XpansionResourceFileType.CONSTRAINTS, "my.txt")

        dao.save_xpansion_constraint({"other.txt": b"x"})
        dao.checks_xpansion_resource_can_be_deleted(XpansionResourceFileType.CONSTRAINTS, "other.txt")  # no raise

    def test_checks_weight_can_be_deleted_raises_if_used_in_settings(self, dao: StudyDao) -> None:
        """checks_xpansion_resource_can_be_deleted should raise if weight file is referenced by settings."""
        dao.create_xpansion_configuration()
        dao.save_xpansion_settings(XpansionSettings(yearly_weights="mc.csv"))

        with pytest.raises(FileCurrentlyUsedInSettings):
            dao.checks_xpansion_resource_can_be_deleted(XpansionResourceFileType.WEIGHTS, "mc.csv")

        dao.checks_xpansion_resource_can_be_deleted(XpansionResourceFileType.WEIGHTS, "unused.csv")  # no raise

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
        self, dao: StudyDao, profile_field: str
    ) -> None:
        """checks_xpansion_resource_can_be_deleted should raise for any of the 6 candidate profile columns."""
        dao.create_xpansion_configuration()
        save_area(dao, "Paris")
        save_area(dao, "Lyon")
        dao.save_links([Link(area1="paris", area2="lyon")])

        candidate = XpansionCandidate(
            name="cand",
            link="lyon - paris",
            annual_cost_per_mw=100.0,
            max_investment=1000.0,
            **{profile_field: "used_capa.txt"},
        )
        dao.save_xpansion_candidate(candidate)

        with pytest.raises(FileCurrentlyUsedInSettings):
            dao.checks_xpansion_resource_can_be_deleted(XpansionResourceFileType.CAPACITIES, "used_capa.txt")

        dao.checks_xpansion_resource_can_be_deleted(XpansionResourceFileType.CAPACITIES, "other.txt")  # no raise
