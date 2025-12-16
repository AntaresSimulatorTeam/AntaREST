# Copyright (c) 2025, RTE (https://www.rte-france.com)
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
Unit tests for DatabaseAreaDao.
"""

import uuid

import pandas as pd
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.core.exceptions import AreaNotFound
from antarest.study.business.model.area_model import AreaUI
from antarest.study.dao.database.database_area_dao import DatabaseAreaDao
from antarest.study.dao.database.models import area, area_ui
from antarest.study.model import StorageMode
from tests.helpers import create_study


class TestDatabaseAreaDao(DatabaseAreaDao):
    """
    Concrete implementation of DatabaseAreaDao for testing.
    Implements the abstract methods
    """

    def __init__(self, study_id: str, session: Session):
        self._study_id = study_id
        self._session = session

    @override
    def get_study_id(self) -> str:
        return self._study_id

    @override
    def get_session(self) -> Session:
        return self._session

    @override
    def get_load(self, area_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    @override
    def get_misc_gen(self, area_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    @override
    def get_reserves(self, area_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    @override
    def get_solar(self, area_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    @override
    def get_wind(self, area_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    @override
    def save_load(self, area_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @override
    def save_misc_gen(self, area_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @override
    def save_reserves(self, area_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @override
    def save_solar(self, area_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @override
    def save_wind(self, area_id: str, series_id: str) -> None:
        raise NotImplementedError()


class TestDatabaseAreaDaoMethods:
    """
    Test suite for DatabaseAreaDao methods.

    Note: The area and area_ui tables are now part of Base.metadata,
    so they're automatically created by the db_engine fixture.
    """

    @pytest.fixture
    def study_id(self, db_session: Session) -> str:
        """Create a test study in database mode and return its ID."""
        study_id = str(uuid.uuid4())
        with db_session:
            study = create_study(id=study_id, name="Test Study")
            study.storage_mode = StorageMode.DATABASE
            db_session.add(study)
            db_session.commit()
        return study_id

    @pytest.fixture
    def dao(self, db_session: Session, study_id: str) -> TestDatabaseAreaDao:
        """Create a DatabaseAreaDao instance for testing."""
        return TestDatabaseAreaDao(study_id, db_session)

    def test_save_area_creates_area_with_default_ui(self, db_session: Session, dao: TestDatabaseAreaDao) -> None:
        """
        Test that save_area creates a new area with default UI for layer '0'.
        """
        with db_session:
            dao.save_area("Paris")
            db_session.commit()

        with db_session:
            # Check area was created
            stmt_area = select(area).where((area.c.study_id == dao.get_study_id()) & (area.c.area_id == "paris"))
            area_row = db_session.execute(stmt_area).fetchone()
            assert area_row is not None
            assert area_row.area_id == "paris"

            # Check default UI was created for layer "0"
            stmt_ui = select(area_ui).where((area_ui.c.area_id == area_row.id) & (area_ui.c.layer_id == "0"))
            ui_row = db_session.execute(stmt_ui).fetchone()
            assert ui_row is not None
            assert ui_row.x == 0
            assert ui_row.y == 0
            assert ui_row.color_r == 230
            assert ui_row.color_g == 108
            assert ui_row.color_b == 44

    def test_save_area_raises_error_if_exists(self, db_session: Session, dao: TestDatabaseAreaDao) -> None:
        """
        Test that save_area raises ValueError if area already exists.
        """
        with db_session:
            dao.save_area("Paris")
            db_session.commit()

        with db_session:
            with pytest.raises(ValueError, match="already exists"):
                dao.save_area("Paris")

    def test_delete_area_removes_area_and_ui(self, db_session: Session, dao: TestDatabaseAreaDao) -> None:
        """
        Test that delete_area removes the area and cascades to area_ui.
        """
        with db_session:
            dao.save_area("Paris")
            db_session.commit()

        with db_session:
            dao.delete_area("paris")
            db_session.commit()

        with db_session:
            # Check area was deleted
            stmt_area = select(area).where((area.c.study_id == dao.get_study_id()) & (area.c.area_id == "paris"))
            area_row = db_session.execute(stmt_area).fetchone()
            assert area_row is None

    def test_delete_area_raises_error_if_not_exists(self, db_session: Session, dao: TestDatabaseAreaDao) -> None:
        """
        Test that delete_area raises AreaNotFound if area doesn't exist.
        """
        with db_session:
            with pytest.raises(AreaNotFound):
                dao.delete_area("nonexistent")

    def test_get_all_areas_info_returns_areas(self, db_session: Session, dao: TestDatabaseAreaDao) -> None:
        """
        Test that get_all_areas_info returns all areas for a study.
        """
        with db_session:
            dao.save_area("Paris")
            dao.save_area("London")
            dao.save_area("Berlin")
            db_session.commit()

        with db_session:
            areas = dao.get_all_areas_info()
            assert len(areas) == 3
            area_ids = {a.id for a in areas}
            assert area_ids == {"paris", "london", "berlin"}
            # All areas should have thermals=None for now
            assert all(a.thermals is None for a in areas)

    def test_get_area_ui_returns_ui_for_layer(self, db_session: Session, dao: TestDatabaseAreaDao) -> None:
        """
        Test that get_area_ui returns UI data for a specific layer.
        """
        with db_session:
            dao.save_area("Paris")
            db_session.commit()

        with db_session:
            # Get default UI
            ui = dao.get_area_ui("paris", "0")
            assert ui.x == 0
            assert ui.y == 0
            assert ui.color_rgb == (230, 108, 44)

    def test_get_area_ui_falls_back_to_layer_zero(self, db_session: Session, dao: TestDatabaseAreaDao) -> None:
        """
        Test that get_area_ui falls back to layer '0' if requested layer doesn't exist.
        """
        with db_session:
            dao.save_area("Paris")
            db_session.commit()

        with db_session:
            # Request non-existent layer, should fall back to layer "0"
            ui = dao.get_area_ui("paris", "99")
            assert ui.x == 0
            assert ui.y == 0
            assert ui.color_rgb == (230, 108, 44)

    def test_get_area_ui_raises_error_if_area_not_exists(self, db_session: Session, dao: TestDatabaseAreaDao) -> None:
        """
        Test that get_area_ui raises AreaNotFound if area doesn't exist.
        """
        with db_session:
            with pytest.raises(AreaNotFound):
                dao.get_area_ui("nonexistent")

    def test_save_area_ui_updates_existing(self, db_session: Session, dao: TestDatabaseAreaDao) -> None:
        """
        Test that save_area_ui updates existing UI data.
        """
        with db_session:
            dao.save_area("Paris")
            db_session.commit()

        with db_session:
            # Update UI
            new_ui = AreaUI(x=100, y=200, color_rgb=(255, 0, 0))
            dao.save_area_ui("paris", "0", new_ui)
            db_session.commit()

        with db_session:
            # Verify update
            ui = dao.get_area_ui("paris", "0")
            assert ui.x == 100
            assert ui.y == 200
            assert ui.color_rgb == (255, 0, 0)

    def test_save_area_ui_creates_new_layer(self, db_session: Session, dao: TestDatabaseAreaDao) -> None:
        """
        Test that save_area_ui creates UI for a new layer.
        """
        with db_session:
            dao.save_area("Paris")
            db_session.commit()

        with db_session:
            # Create UI for layer "1"
            layer1_ui = AreaUI(x=300, y=400, color_rgb=(0, 255, 0))
            dao.save_area_ui("paris", "1", layer1_ui)
            db_session.commit()

        with db_session:
            # Verify layer "0" is unchanged
            ui_layer0 = dao.get_area_ui("paris", "0")
            assert ui_layer0.x == 0
            assert ui_layer0.y == 0

            # Verify layer "1" was created
            ui_layer1 = dao.get_area_ui("paris", "1")
            assert ui_layer1.x == 300
            assert ui_layer1.y == 400
            assert ui_layer1.color_rgb == (0, 255, 0)

    def test_save_area_ui_raises_error_if_area_not_exists(self, db_session: Session, dao: TestDatabaseAreaDao) -> None:
        """
        Test that save_area_ui raises AreaNotFound if area doesn't exist.
        """
        with db_session:
            new_ui = AreaUI(x=100, y=200, color_rgb=(255, 0, 0))
            with pytest.raises(AreaNotFound):
                dao.save_area_ui("nonexistent", "0", new_ui)

    def test_get_all_areas_ui_info_returns_all_layers(self, db_session: Session, dao: TestDatabaseAreaDao) -> None:
        """
        Test that get_all_areas_ui_info returns UI data for all areas and layers.
        """
        with db_session:
            dao.save_area("Paris")
            dao.save_area("London")
            db_session.commit()

        with db_session:
            # Add UI for different layers
            dao.save_area_ui("paris", "1", AreaUI(x=100, y=100, color_rgb=(255, 0, 0)))
            dao.save_area_ui("paris", "2", AreaUI(x=200, y=200, color_rgb=(0, 255, 0)))
            dao.save_area_ui("london", "1", AreaUI(x=150, y=150, color_rgb=(0, 0, 255)))
            db_session.commit()

        with db_session:
            all_ui = dao.get_all_areas_ui_info()
            assert len(all_ui) == 2
            assert "paris" in all_ui
            assert "london" in all_ui

            # Check Paris UI data
            paris_ui = all_ui["paris"]
            assert paris_ui.ui["x"] == 0
            assert paris_ui.ui["y"] == 0
            assert paris_ui.ui["layers"] == "1 2"
            assert paris_ui.layer_x == {"0": 0, "1": 100, "2": 200}
            assert paris_ui.layer_y == {"0": 0, "1": 100, "2": 200}
            assert paris_ui.layer_color == {"0": "230, 108, 44", "1": "255, 0, 0", "2": "0, 255, 0"}

            # Check London UI data
            london_ui = all_ui["london"]
            assert london_ui.ui["x"] == 0
            assert london_ui.ui["y"] == 0
            assert london_ui.ui["layers"] == "1"
            assert london_ui.layer_x == {"0": 0, "1": 150}
            assert london_ui.layer_y == {"0": 0, "1": 150}
            assert london_ui.layer_color == {"0": "230, 108, 44", "1": "0, 0, 255"}

    def test_save_layer_areas_adds_and_removes(self, db_session: Session, dao: TestDatabaseAreaDao) -> None:
        """
        Test that save_layer_areas adds and removes areas from a layer.
        """
        with db_session:
            dao.save_area("Paris")
            dao.save_area("London")
            dao.save_area("Berlin")
            db_session.commit()

        with db_session:
            # Associate Paris and London with layer "1"
            dao.save_layer_areas("1", ["paris", "london"])
            db_session.commit()

        with db_session:
            # Verify Paris and London have layer "1"
            paris_ui = dao.get_area_ui("paris", "1")
            assert paris_ui is not None
            london_ui = dao.get_area_ui("london", "1")
            assert london_ui is not None

            # Verify Berlin doesn't have layer "1"
            # (should fall back to layer "0")
            stmt_area = select(area.c.id).where((area.c.study_id == dao.get_study_id()) & (area.c.area_id == "berlin"))
            berlin_area_row = db_session.execute(stmt_area).fetchone()
            assert berlin_area_row is not None
            stmt_ui = select(area_ui).where((area_ui.c.area_id == berlin_area_row.id) & (area_ui.c.layer_id == "1"))
            berlin_layer1 = db_session.execute(stmt_ui).fetchone()
            assert berlin_layer1 is None

        with db_session:
            # Update layer "1" to only have Berlin
            dao.save_layer_areas("1", ["berlin"])
            db_session.commit()

        with db_session:
            # Verify Paris and London no longer have layer "1"
            stmt_area_paris = select(area.c.id).where(
                (area.c.study_id == dao.get_study_id()) & (area.c.area_id == "paris")
            )
            paris_area_row = db_session.execute(stmt_area_paris).fetchone()
            assert paris_area_row is not None
            stmt_ui_paris = select(area_ui).where(
                (area_ui.c.area_id == paris_area_row.id) & (area_ui.c.layer_id == "1")
            )
            paris_layer1 = db_session.execute(stmt_ui_paris).fetchone()
            assert paris_layer1 is None

            stmt_area_london = select(area.c.id).where(
                (area.c.study_id == dao.get_study_id()) & (area.c.area_id == "london")
            )
            london_area_row = db_session.execute(stmt_area_london).fetchone()
            assert london_area_row is not None
            stmt_ui_london = select(area_ui).where(
                (area_ui.c.area_id == london_area_row.id) & (area_ui.c.layer_id == "1")
            )
            london_layer1 = db_session.execute(stmt_ui_london).fetchone()
            assert london_layer1 is None

            # Verify Berlin has layer "1"
            berlin_ui = dao.get_area_ui("berlin", "1")
            assert berlin_ui is not None

    def test_save_layer_areas_copies_default_ui(self, db_session: Session, dao: TestDatabaseAreaDao) -> None:
        """
        Test that save_layer_areas copies default UI from layer '0' when adding areas to a new layer.
        """
        with db_session:
            dao.save_area("Paris")
            # Update layer "0" UI to non-default values
            dao.save_area_ui("paris", "0", AreaUI(x=50, y=75, color_rgb=(100, 150, 200)))
            db_session.commit()

        with db_session:
            # Add Paris to layer "1"
            dao.save_layer_areas("1", ["paris"])
            db_session.commit()

        with db_session:
            # Verify layer "1" copied UI from layer "0"
            layer1_ui = dao.get_area_ui("paris", "1")
            assert layer1_ui.x == 50
            assert layer1_ui.y == 75
            assert layer1_ui.color_rgb == (100, 150, 200)
