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
Unit tests for DatabaseAreaDao.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from antarest.core.exceptions import AreaNotFound, LayerNotFound
from antarest.study.business.model.area_model import AreaUI
from antarest.study.business.model.layer_model import Layer
from antarest.study.business.model.thermal_cluster_model import ThermalCluster
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.dao.database.models.area import AREA_TABLE, AREA_UI_TABLE


def test_save_area_creates_area_with_default_ui(db_session: Session, dao: DatabaseStudyDao) -> None:
    """
    Test that save_area creates a new area with default UI for layer '0'.
    """
    dao.save_area("Paris")

    study_id = dao.get_study_id()

    with db_session:
        # Check area was created with both ID and original name
        stmt_area = select(AREA_TABLE).where((AREA_TABLE.c.study_id == study_id) & (AREA_TABLE.c.area_id == "paris"))
        area_row = db_session.execute(stmt_area).fetchone()
        assert area_row is not None
        assert area_row.area_id == "paris"
        assert area_row.area_name == "Paris"

        # Check default UI was created for layer "0"
        stmt_ui = select(AREA_UI_TABLE).where(
            (AREA_UI_TABLE.c.study_id == study_id)
            & (AREA_UI_TABLE.c.area_id == "paris")
            & (AREA_UI_TABLE.c.layer_id == "0")
        )
        ui_row = db_session.execute(stmt_ui).fetchone()
        assert ui_row is not None
        assert ui_row.x == 0
        assert ui_row.y == 0
        assert ui_row.color_r == 230
        assert ui_row.color_g == 108
        assert ui_row.color_b == 44


def test_save_area_raises_error_if_exists(dao: DatabaseStudyDao) -> None:
    """
    Test that save_area raises ValueError if area already exists.
    """
    dao.save_area("Paris")

    with pytest.raises(ValueError, match="already exists"):
        dao.save_area("Paris")


def test_delete_area_removes_area_and_ui(db_session: Session, dao: DatabaseStudyDao) -> None:
    """
    Test that delete_area removes the area and cascades to area_ui.
    """
    dao.save_area("Paris")
    dao.delete_area("paris")

    with db_session:
        # Check area was deleted
        stmt_area = select(AREA_TABLE).where(
            (AREA_TABLE.c.study_id == dao.get_study_id()) & (AREA_TABLE.c.area_id == "paris")
        )
        area_row = db_session.execute(stmt_area).fetchone()
        assert area_row is None


def test_delete_area_raises_error_if_not_exists(dao: DatabaseStudyDao) -> None:
    """
    Test that delete_area raises AreaNotFound if area doesn't exist.
    """
    with pytest.raises(AreaNotFound):
        dao.delete_area("nonexistent")


def test_get_all_areas_info_returns_areas(dao: DatabaseStudyDao) -> None:
    """
    Test that get_all_areas_info returns all areas for a study with original names preserved.
    """
    dao.save_area("Paris")
    dao.save_area("London")
    dao.save_area("Berlin")
    dao.save_thermal("paris", ThermalCluster(id="gas", name="Gas"))
    dao.save_thermal("berlin", ThermalCluster(id="coal", name="Coal"))

    areas = dao.get_all_areas_info()
    assert len(areas) == 3
    # Check IDs (lowercase/normalized)
    area_ids = {a.id for a in areas}
    assert area_ids == {"paris", "london", "berlin"}
    # Check original names are preserved
    area_names = {a.name for a in areas}
    assert area_names == {"Paris", "London", "Berlin"}
    areas_by_id = {area.id: area for area in areas}
    assert [thermal.id for thermal in areas_by_id["paris"].thermals] == ["gas"]
    assert [thermal.id for thermal in areas_by_id["berlin"].thermals] == ["coal"]
    assert areas_by_id["london"].thermals == []


def test_get_area_ui_returns_ui_for_layer(dao: DatabaseStudyDao) -> None:
    """
    Test that get_area_ui returns UI data for a specific layer.
    """
    dao.save_area("Paris")

    # Get default UI
    ui = dao.get_area_ui("paris", "0")
    assert ui.x == 0
    assert ui.y == 0
    assert ui.color_rgb == (230, 108, 44)


def test_get_area_ui_falls_back_to_layer_zero(dao: DatabaseStudyDao) -> None:
    """
    Test that get_area_ui falls back to layer '0' if requested layer doesn't exist.
    """
    dao.save_area("Paris")

    # Request non-existent layer, should fall back to layer "0"
    ui = dao.get_area_ui("paris", "99")
    assert ui.x == 0
    assert ui.y == 0
    assert ui.color_rgb == (230, 108, 44)


def test_get_area_ui_raises_error_if_area_not_exists(dao: DatabaseStudyDao) -> None:
    """
    Test that get_area_ui raises AreaNotFound if area doesn't exist.
    """
    with pytest.raises(AreaNotFound):
        dao.get_area_ui("nonexistent")


def test_save_area_ui_updates_existing(dao: DatabaseStudyDao) -> None:
    """
    Test that save_area_ui updates existing UI data.
    """
    dao.save_area("Paris")

    # Update UI
    new_ui = AreaUI(x=100, y=200, color_rgb=(255, 0, 0))
    dao.save_area_ui("paris", "0", new_ui)

    # Verify update
    ui = dao.get_area_ui("paris", "0")
    assert ui.x == 100
    assert ui.y == 200
    assert ui.color_rgb == (255, 0, 0)


def test_save_area_ui_creates_new_layer(dao: DatabaseStudyDao) -> None:
    """
    Test that save_area_ui creates UI for a new layer.
    """
    dao.save_area("Paris")
    dao.save_layer(Layer(id="1", name="Layer 1"))

    # Create UI for layer "1"
    layer1_ui = AreaUI(x=300, y=400, color_rgb=(0, 255, 0))
    dao.save_area_ui("paris", "1", layer1_ui)

    # Verify layer "0" is unchanged
    ui_layer0 = dao.get_area_ui("paris", "0")
    assert ui_layer0.x == 0
    assert ui_layer0.y == 0

    # Verify layer "1" was created
    ui_layer1 = dao.get_area_ui("paris", "1")
    assert ui_layer1.x == 300
    assert ui_layer1.y == 400
    assert ui_layer1.color_rgb == (0, 255, 0)


def test_save_area_ui_raises_error_if_area_not_exists(dao: DatabaseStudyDao) -> None:
    """
    Test that save_area_ui raises AreaNotFound if area doesn't exist.
    """
    new_ui = AreaUI(x=100, y=200, color_rgb=(255, 0, 0))
    with pytest.raises(AreaNotFound):
        dao.save_area_ui("nonexistent", "0", new_ui)


def test_save_area_ui_raises_error_if_layer_not_exists(dao: DatabaseStudyDao) -> None:
    """
    Test that save_area_ui raises LayerNotFound if layer doesn't exist.
    """
    dao.save_area("Paris")
    new_ui = AreaUI(x=100, y=200, color_rgb=(255, 0, 0))
    with pytest.raises(LayerNotFound):
        dao.save_area_ui("paris", "999", new_ui)


def test_get_all_areas_ui_info_returns_all_layers(dao: DatabaseStudyDao) -> None:
    """
    Test that get_all_areas_ui_info returns UI data for all areas and layers.
    """
    dao.save_area("Paris")
    dao.save_area("London")
    dao.save_layer(Layer(id="1", name="Layer 1"))
    dao.save_layer(Layer(id="2", name="Layer 2"))

    # Add UI for different layers
    dao.save_area_ui("paris", "1", AreaUI(x=100, y=100, color_rgb=(255, 0, 0)))
    dao.save_area_ui("paris", "2", AreaUI(x=200, y=200, color_rgb=(0, 255, 0)))
    dao.save_area_ui("london", "1", AreaUI(x=150, y=150, color_rgb=(0, 0, 255)))

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


def test_save_layer_areas_adds_and_removes(db_session: Session, dao: DatabaseStudyDao) -> None:
    """
    Test that save_layer_areas adds and removes areas from a layer.
    """
    dao.save_area("Paris")
    dao.save_area("London")
    dao.save_area("Berlin")
    dao.save_layer(Layer(id="1", name="Layer 1"))

    dao.save_layer_areas("1", ["paris", "london"])

    with db_session:
        # Verify Berlin doesn't have layer "1"
        # (should fall back to layer "0")
        study_id = dao.get_study_id()
        stmt_ui = select(AREA_UI_TABLE).where(
            (AREA_UI_TABLE.c.study_id == study_id)
            & (AREA_UI_TABLE.c.area_id == "berlin")
            & (AREA_UI_TABLE.c.layer_id == "1")
        )
        berlin_layer1 = db_session.execute(stmt_ui).fetchone()
        assert berlin_layer1 is None

    # Update layer "1" to only have Berlin
    dao.save_layer_areas("1", ["berlin"])

    with db_session:
        # Verify Paris and London no longer have layer "1"
        study_id = dao.get_study_id()
        stmt_ui_paris = select(AREA_UI_TABLE).where(
            (AREA_UI_TABLE.c.study_id == study_id)
            & (AREA_UI_TABLE.c.area_id == "paris")
            & (AREA_UI_TABLE.c.layer_id == "1")
        )
        paris_layer1 = db_session.execute(stmt_ui_paris).fetchone()
        assert paris_layer1 is None

        stmt_ui_london = select(AREA_UI_TABLE).where(
            (AREA_UI_TABLE.c.study_id == study_id)
            & (AREA_UI_TABLE.c.area_id == "london")
            & (AREA_UI_TABLE.c.layer_id == "1")
        )
        london_layer1 = db_session.execute(stmt_ui_london).fetchone()
        assert london_layer1 is None


def test_save_layer_areas_copies_default_ui(dao: DatabaseStudyDao) -> None:
    """
    Test that save_layer_areas copies default UI from layer '0' when adding areas to a new layer.
    """
    dao.save_area("Paris")
    dao.save_layer(Layer(id="1", name="Layer 1"))
    # Update layer "0" UI to non-default values
    dao.save_area_ui("paris", "0", AreaUI(x=50, y=75, color_rgb=(100, 150, 200)))

    # Add Paris to layer "1"
    dao.save_layer_areas("1", ["paris"])

    # Verify layer "1" copied UI from layer "0"
    layer1_ui = dao.get_area_ui("paris", "1")
    assert layer1_ui.x == 50
    assert layer1_ui.y == 75
    assert layer1_ui.color_rgb == (100, 150, 200)
