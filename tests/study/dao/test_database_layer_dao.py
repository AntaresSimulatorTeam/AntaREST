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
Unit tests for DatabaseLayerDao.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from antarest.core.exceptions import LayerNotAllowedToBeDeleted, LayerNotFound
from antarest.study.business.model.layer_model import Layer
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.dao.database.models.area import AREA_UI_TABLE
from tests.study.dao.utils import save_area


class TestInitializeStudy:
    def test_initialize_study_creates_default_layer(self, db_dao: DatabaseStudyDao) -> None:
        """Test that the DAO is initialized with the default 'All' layer in an empty study."""
        dao = db_dao
        assert dao.get_layers() == [Layer(id="0", name="All", areas=[])]


class TestDatabaseLayerDao:
    def test_get_layers_returns_default_layer(self, db_dao: DatabaseStudyDao) -> None:
        dao = db_dao
        layers = dao.get_layers()
        assert len(layers) == 1
        assert layers[0].id == "0"
        assert layers[0].name == "All"
        assert layers[0].areas == []

    def test_get_layers_with_areas(self, db_dao: DatabaseStudyDao) -> None:
        dao = db_dao
        save_area(dao, "Paris")
        save_area(dao, "London")

        layers = dao.get_layers()
        assert len(layers) == 1
        assert layers[0].id == "0"
        assert set(layers[0].areas) == {"paris", "london"}

    def test_save_layer_creates_layer(self, db_dao: DatabaseStudyDao) -> None:
        dao = db_dao
        layer = Layer(id="1", name="Layer 1")
        dao.save_layer(layer)

        assert dao.layer_exists("1")
        layers = dao.get_layers()
        layer_1 = next((layer for layer in layers if layer.id == "1"), None)
        assert layer_1 is not None
        assert layer_1.name == "Layer 1"

    def test_save_layer_with_areas(self, db_dao: DatabaseStudyDao) -> None:
        dao = db_dao
        save_area(dao, "Paris")
        save_area(dao, "London")

        layer = Layer(id="1", name="Layer 1", areas=["paris", "london"])
        dao.save_layer(layer)

        layers = dao.get_layers()
        layer_1 = next((layer for layer in layers if layer.id == "1"), None)
        assert layer_1 is not None
        assert set(layer_1.areas) == {"paris", "london"}

    def test_save_layer_updates_existing(self, db_dao: DatabaseStudyDao) -> None:
        dao = db_dao
        dao.save_layer(Layer(id="1", name="Layer 1"))
        dao.save_layer(Layer(id="1", name="Layer 1 Updated"))

        layers = dao.get_layers()
        layer_1 = next((layer for layer in layers if layer.id == "1"), None)
        assert layer_1 is not None
        assert layer_1.name == "Layer 1 Updated"

    def test_save_layer_updates_areas(self, db_dao: DatabaseStudyDao) -> None:
        dao = db_dao
        save_area(dao, "Paris")
        save_area(dao, "London")
        save_area(dao, "Berlin")

        dao.save_layer(Layer(id="1", name="Layer 1", areas=["paris", "london"]))
        dao.save_layer(Layer(id="1", name="Layer 1", areas=["paris", "berlin"]))

        layers = dao.get_layers()
        layer_1 = next((layer for layer in layers if layer.id == "1"), None)
        assert layer_1 is not None
        assert set(layer_1.areas) == {"paris", "berlin"}

    def test_delete_layer(self, db_dao: DatabaseStudyDao) -> None:
        dao = db_dao
        dao.save_layer(Layer(id="1", name="Layer 1"))
        assert dao.layer_exists("1")

        dao.delete_layer(layer_id="1")
        assert not dao.layer_exists("1")

    def test_delete_layer_removes_area_associations(self, db_dao: DatabaseStudyDao, db_session: Session) -> None:
        dao = db_dao
        study_id = dao.get_study_id()
        save_area(dao, "Paris")
        save_area(dao, "London")

        dao.save_layer(Layer(id="1", name="Layer 1", areas=["paris", "london"]))
        dao.delete_layer(layer_id="1")

        layers = dao.get_layers()
        assert len(layers) == 1
        assert layers[0].id == "0"

        stmt = select(AREA_UI_TABLE).where((AREA_UI_TABLE.c.study_id == study_id) & (AREA_UI_TABLE.c.layer_id == "1"))
        remaining_entries = db_session.execute(stmt).fetchall()
        assert remaining_entries == []

    def test_delete_layer_raises_if_not_found(self, db_dao: DatabaseStudyDao) -> None:
        with pytest.raises(LayerNotFound):
            db_dao.delete_layer(layer_id="999")

    def test_delete_default_layer_raises(self, db_dao: DatabaseStudyDao) -> None:
        with pytest.raises(LayerNotAllowedToBeDeleted):
            db_dao.delete_layer(layer_id="0")

    def test_layer_exists_default_layer(self, db_dao: DatabaseStudyDao) -> None:
        assert db_dao.layer_exists("0")

    def test_layer_exists_returns_false_for_nonexistent(self, db_dao: DatabaseStudyDao) -> None:
        assert not db_dao.layer_exists("999")

    def test_multiple_layers(self, db_dao: DatabaseStudyDao) -> None:
        dao = db_dao
        save_area(dao, "Paris")
        save_area(dao, "London")
        save_area(dao, "Berlin")

        dao.save_layer(Layer(id="1", name="Layer 1", areas=["paris"]))
        dao.save_layer(Layer(id="2", name="Layer 2", areas=["london", "berlin"]))

        layers = dao.get_layers()
        assert len(layers) == 3

        layer_0 = next(layer for layer in layers if layer.id == "0")
        layer_1 = next(layer for layer in layers if layer.id == "1")
        layer_2 = next(layer for layer in layers if layer.id == "2")

        assert set(layer_0.areas) == {"paris", "london", "berlin"}
        assert layer_1.areas == ["paris"]
        assert set(layer_2.areas) == {"london", "berlin"}

    def test_delete_area_removes_from_layers(self, db_dao: DatabaseStudyDao) -> None:
        dao = db_dao
        save_area(dao, "Paris")
        save_area(dao, "London")

        dao.save_layer(Layer(id="1", name="Layer 1", areas=["paris", "london"]))

        dao.delete_area("paris")

        layers = dao.get_layers()
        layer_1 = next(layer for layer in layers if layer.id == "1")
        assert layer_1.areas == ["london"]
