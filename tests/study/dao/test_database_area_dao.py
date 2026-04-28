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

from antarest.core.exceptions import AreaNotFound, LayerNotFound
from antarest.study.business.model.area_model import AreaUI
from antarest.study.business.model.layer_model import Layer
from antarest.study.business.model.thermal_cluster_model import ThermalCluster
from antarest.study.dao.api.study_dao import StudyDao
from tests.study.dao.conftest import create_area
from tests.study.dao.utils import save_area


def test_create_area_with_default_ui(dao: StudyDao) -> None:
    """
    Test that the `CreateArea` command creates a new area with the default UI for layer '0'.
    """
    create_area("Paris", dao)

    # Check area was created with both ID and original name
    areas = dao.get_all_areas_info()
    area_row = next(area for area in areas if area.name == "Paris")
    assert area_row.id == "paris"
    assert area_row.name == "Paris"

    # Check default UI was created for layer "0"
    ui_row = dao.get_area_ui(area_row.id)
    assert ui_row.x == 0
    assert ui_row.y == 0
    assert ui_row.color_rgb == (230, 108, 44)


def test_save_area_raises_error_if_exists(dao: StudyDao) -> None:
    """
    Test that save_area raises ValueError if area already exists.
    """
    save_area(dao, "Paris")

    with pytest.raises(ValueError, match="already exist"):
        save_area(dao, "Paris")


def test_delete_area_removes_area_and_ui(dao: StudyDao) -> None:
    """
    Test that delete_area removes the area and cascades to area_ui.
    """
    save_area(dao, "Paris")
    dao.delete_area("paris")

    # Check area was deleted
    assert dao.get_all_area_ids() == []


def test_delete_area_raises_error_if_not_exists(dao: StudyDao) -> None:
    """
    Test that delete_area raises AreaNotFound if area doesn't exist.
    """
    with pytest.raises(AreaNotFound):
        dao.delete_area("nonexistent")


def test_get_all_areas_info_returns_areas(dao: StudyDao) -> None:
    """
    Test that get_all_areas_info returns all areas for a study with original names preserved.
    """
    save_area(dao, "Paris")
    save_area(dao, "London")
    save_area(dao, "Berlin")
    dao.save_thermals({"paris": [ThermalCluster(name="gas")], "berlin": [ThermalCluster(name="coal")]})

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


def test_get_area_ui_returns_ui_for_layer(dao: StudyDao) -> None:
    """
    Test that get_area_ui returns UI data for a specific layer.
    """
    save_area(dao, "Paris")

    # Get default UI
    ui = dao.get_area_ui("paris", "0")
    assert ui.x == 0
    assert ui.y == 0
    assert ui.color_rgb == (230, 108, 44)


def test_get_area_ui_falls_back_to_layer_zero(dao: StudyDao) -> None:
    """
    Test that get_area_ui falls back to layer '0' if requested layer doesn't exist.
    """
    save_area(dao, "Paris")

    # Request non-existent layer, should fall back to layer "0"
    ui = dao.get_area_ui("paris", "99")
    assert ui.x == 0
    assert ui.y == 0
    assert ui.color_rgb == (230, 108, 44)


def test_get_area_ui_raises_error_if_area_not_exists(dao: StudyDao) -> None:
    """
    Test that get_area_ui raises AreaNotFound if area doesn't exist.
    """
    with pytest.raises(AreaNotFound):
        dao.get_area_ui("nonexistent")


def test_save_area_ui_updates_existing(dao: StudyDao) -> None:
    """
    Test that save_area_ui updates existing UI data.
    """
    save_area(dao, "Paris")

    # Update UI
    new_ui = AreaUI(x=100, y=200, color_rgb=(255, 0, 0))
    dao.save_area_ui({"paris": {"0": new_ui}})

    # Verify update
    ui = dao.get_area_ui("paris", "0")
    assert ui.x == 100
    assert ui.y == 200
    assert ui.color_rgb == (255, 0, 0)


def test_save_area_ui_creates_new_layer(dao: StudyDao) -> None:
    """
    Test that save_area_ui creates UI for a new layer.
    """
    save_area(dao, "Paris")
    dao.save_layer(Layer(id="1", name="Layer 1"))

    # Create UI for layer "1"
    layer1_ui = AreaUI(x=300, y=400, color_rgb=(0, 255, 0))
    dao.save_area_ui({"paris": {"1": layer1_ui}})

    # Verify layer "0" is unchanged
    ui_layer0 = dao.get_area_ui("paris", "0")
    assert ui_layer0.x == 0
    assert ui_layer0.y == 0

    # Verify layer "1" was created
    ui_layer1 = dao.get_area_ui("paris", "1")
    assert ui_layer1.x == 300
    assert ui_layer1.y == 400
    assert ui_layer1.color_rgb == (0, 255, 0)


def test_save_area_ui_raises_error_if_area_not_exists(dao: StudyDao) -> None:
    """
    Test that save_area_ui raises AreaNotFound if area doesn't exist.
    """
    new_ui = AreaUI(x=100, y=200, color_rgb=(255, 0, 0))
    with pytest.raises(AreaNotFound):
        dao.save_area_ui({"nonexistent": {"0": new_ui}})


def test_save_area_ui_raises_error_if_layer_not_exists(dao: StudyDao) -> None:
    """
    Test that save_area_ui raises LayerNotFound if layer doesn't exist.
    """
    save_area(dao, "Paris")
    new_ui = AreaUI(x=100, y=200, color_rgb=(255, 0, 0))
    with pytest.raises(LayerNotFound):
        dao.save_area_ui({"paris": {"999": new_ui}})


def test_get_all_areas_ui_info_returns_all_layers(dao: StudyDao) -> None:
    """
    Test that get_all_areas_ui_info returns UI data for all areas and layers.
    """
    create_area("Paris", dao)
    create_area("London", dao)
    dao.save_layer(Layer(id="1", name="Layer 1"))
    dao.save_layer(Layer(id="2", name="Layer 2"))

    dao.save_layer_areas("1", ["paris", "london"])
    dao.save_layer_areas("2", ["paris"])

    # Add UI for different layers
    dao.save_area_ui(
        {
            "paris": {
                "1": AreaUI(x=100, y=100, color_rgb=(255, 0, 0)),
                "2": AreaUI(x=200, y=200, color_rgb=(0, 255, 0)),
            },
            "london": {"1": AreaUI(x=150, y=150, color_rgb=(0, 0, 255))},
        }
    )

    all_ui = dao.get_all_areas_ui_info()
    assert len(all_ui) == 2
    assert "paris" in all_ui
    assert "london" in all_ui

    # Check Paris UI data
    paris_ui = all_ui["paris"]
    assert paris_ui.ui["x"] == 0
    assert paris_ui.ui["y"] == 0
    assert paris_ui.ui["layers"] == "0 1 2"
    assert paris_ui.layer_x == {"0": 0, "1": 100, "2": 200}
    assert paris_ui.layer_y == {"0": 0, "1": 100, "2": 200}
    assert paris_ui.layer_color == {"0": "230, 108, 44", "1": "255, 0, 0", "2": "0, 255, 0"}

    # Check London UI data
    london_ui = all_ui["london"]
    assert london_ui.ui["x"] == 0
    assert london_ui.ui["y"] == 0
    assert london_ui.ui["layers"] == "0 1"
    assert london_ui.layer_x == {"0": 0, "1": 150}
    assert london_ui.layer_y == {"0": 0, "1": 150}
    assert london_ui.layer_color == {"0": "230, 108, 44", "1": "0, 0, 255"}


def test_save_layer_areas_adds_and_removes(dao: StudyDao) -> None:
    """
    Test that save_layer_areas adds and removes areas from a layer.
    """
    create_area("Paris", dao)
    create_area("London", dao)
    create_area("Berlin", dao)
    dao.save_layer(Layer(id="1", name="Layer 1"))

    dao.save_layer_areas("1", ["paris", "london"])

    # Berlin not in layer "1"
    all_ui = dao.get_all_areas_ui_info()
    assert "1" not in all_ui["berlin"].layer_x

    # Update layer "1" to only have Berlin
    dao.save_layer_areas("1", ["berlin"])

    # Paris and London no longer in layer "1"
    all_ui = dao.get_all_areas_ui_info()
    assert "1" not in all_ui["paris"].layer_x
    assert "1" not in all_ui["london"].layer_x


def test_save_layer_areas_copies_default_ui(dao: StudyDao) -> None:
    """
    Test that save_layer_areas copies default UI from layer '0' when adding areas to a new layer.
    """
    save_area(dao, "Paris")
    dao.save_layer(Layer(id="1", name="Layer 1"))
    # Update layer "0" UI to non-default values
    dao.save_area_ui({"paris": {"0": AreaUI(x=50, y=75, color_rgb=(100, 150, 200))}})

    # Add Paris to layer "1"
    dao.save_layer_areas("1", ["paris"])

    # Verify layer "1" copied UI from layer "0"
    layer1_ui = dao.get_area_ui("paris", "1")
    assert layer1_ui.x == 50
    assert layer1_ui.y == 75
    assert layer1_ui.color_rgb == (100, 150, 200)
