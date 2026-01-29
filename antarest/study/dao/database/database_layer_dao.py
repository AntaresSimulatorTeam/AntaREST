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
Database implementation of LayerDao.

This module provides database-backed storage for layers when storage_mode=DATABASE.
"""

from abc import abstractmethod
from collections import defaultdict
from typing import TYPE_CHECKING, Sequence

from sqlalchemy import delete, insert, select, update
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.core.exceptions import LayerNotFound
from antarest.study.business.model.area_model import DEFAULT_LAYER_ID
from antarest.study.business.model.layer_model import Layer
from antarest.study.dao.api.layer_dao import LayerDao
from antarest.study.dao.database.models.area import AREA_UI_TABLE
from antarest.study.dao.database.models.layer import LAYER_TABLE

if TYPE_CHECKING:
    from antarest.study.dao.database.database_study_dao import DatabaseStudyDao


class DatabaseLayerDao(LayerDao):
    """
    Database implementation of LayerDao.
    """

    def __init__(self, study_id: str, db_session: Session) -> None:
        """
        Initialize DatabaseLayerDao with dependencies.

        Args:
            study_id: The study ID for database queries.
            db_session: SQLAlchemy session for database operations.
        """
        self._study_id = study_id
        self._db_session = db_session

    def get_study_id(self) -> str:
        """Get the study ID for database queries."""
        return self._study_id

    def get_session(self) -> Session:
        """Get the SQLAlchemy session for database operations."""
        return self._db_session

    @abstractmethod
    def get_impl(self) -> "DatabaseStudyDao":
        pass

    @override
    def get_layers(self) -> Sequence[Layer]:
        """
        Returns the list of layers in this study.

        The default layer (id="0") always contains all areas.
        Other layers contain the areas that have UI entries for that layer.
        """
        study_id = self.get_study_id()
        session = self.get_session()

        # Get all layer names from LAYER_TABLE
        stmt_layers = select(LAYER_TABLE).where(LAYER_TABLE.c.study_id == study_id)
        layer_rows = session.execute(stmt_layers).fetchall()
        layer_names = {row.layer_id: row.name for row in layer_rows}

        # Get all area-layer associations from AREA_UI_TABLE
        stmt_area_ui = select(AREA_UI_TABLE.c.layer_id, AREA_UI_TABLE.c.area_id).where(
            AREA_UI_TABLE.c.study_id == study_id
        )
        area_ui_rows = session.execute(stmt_area_ui).fetchall()

        # Build areas per layer
        areas_by_layer: dict[str, list[str]] = defaultdict(list)
        all_areas: set[str] = set()
        for row in area_ui_rows:
            all_areas.add(row.area_id)
            areas_by_layer[row.layer_id].append(row.area_id)

        # Build result - ensure default layer is first and contains all areas
        layers: list[Layer] = []

        # Default layer (always exists, always contains all areas)
        default_name = layer_names.get(DEFAULT_LAYER_ID, "All")
        layers.append(Layer(id=DEFAULT_LAYER_ID, name=default_name, areas=sorted(all_areas)))

        # Other layers
        for layer_id in sorted(layer_names.keys()):
            if layer_id == DEFAULT_LAYER_ID:
                continue
            name = layer_names.get(layer_id)
            areas = areas_by_layer.get(layer_id, [])
            layers.append(Layer(id=layer_id, name=name, areas=sorted(areas)))

        return layers

    @override
    def save_layer(self, layer: Layer) -> None:
        """
        Save a layer to a study.

        If the layer already exists, it will be updated.
        If areas are provided, the area associations will be updated.
        """
        study_id = self.get_study_id()
        session = self.get_session()

        # Check if layer already exists
        stmt_check = select(LAYER_TABLE.c.layer_id).where(
            (LAYER_TABLE.c.study_id == study_id) & (LAYER_TABLE.c.layer_id == layer.id)
        )
        existing = session.execute(stmt_check).fetchone()

        if existing:
            if layer.name is not None:
                session.execute(
                    update(LAYER_TABLE)
                    .where((LAYER_TABLE.c.study_id == study_id) & (LAYER_TABLE.c.layer_id == layer.id))
                    .values(name=layer.name)
                )
        else:
            session.execute(
                insert(LAYER_TABLE).values(
                    study_id=study_id,
                    layer_id=layer.id,
                    name=layer.name or "",
                )
            )

        # Update area associations if areas are provided
        if layer.areas is not None:
            self.get_impl().save_layer_areas(layer.id, layer.areas)

        session.commit()

    @override
    def delete_layer(self, layer: Layer) -> None:
        """
        Delete a layer from a study.

        This removes the layer name and all area-layer associations for this layer.
        """
        if not self.layer_exists(layer.id):
            raise LayerNotFound()

        study_id = self.get_study_id()
        session = self.get_session()

        # Delete layer name
        session.execute(
            delete(LAYER_TABLE).where((LAYER_TABLE.c.study_id == study_id) & (LAYER_TABLE.c.layer_id == layer.id))
        )

        # Delete all area-layer associations for this layer
        session.execute(
            delete(AREA_UI_TABLE).where((AREA_UI_TABLE.c.study_id == study_id) & (AREA_UI_TABLE.c.layer_id == layer.id))
        )
        session.commit()

    @override
    def layer_exists(self, layer_id: str) -> bool:
        """
        Returns whether a layer with the given id exists in the study.

        The default layer (id="0") always exists.
        """
        # Default layer always exists
        if layer_id == DEFAULT_LAYER_ID:
            return True

        study_id = self.get_study_id()
        session = self.get_session()

        # Check if layer exists in LAYER_TABLE
        stmt = select(LAYER_TABLE.c.layer_id).where(
            (LAYER_TABLE.c.study_id == study_id) & (LAYER_TABLE.c.layer_id == layer_id)
        )
        return session.execute(stmt).fetchone() is not None
