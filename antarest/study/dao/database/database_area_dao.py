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
Database implementation of AreaDao using SQLAlchemy Core.

This module provides database-backed storage for areas when storage_mode=DATABASE.
"""

from abc import abstractmethod
from typing import Any, Dict, List

from sqlalchemy import delete, insert, select, update
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.core.exceptions import AreaNotFound
from antarest.study.business.model.area_model import AreaInfo, AreaUI, AreaUIData
from antarest.study.dao.api.area_dao import AreaDao
from antarest.study.dao.database.models import area, area_ui
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id


class DatabaseAreaDao(AreaDao):
    """
    Database implementation of AreaDao
    """

    @abstractmethod
    def get_study_id(self) -> str:
        """Get the study ID for database queries."""
        raise NotImplementedError()

    @abstractmethod
    def get_session(self) -> Session:
        """Get the SQLAlchemy session for database operations."""
        raise NotImplementedError()

    @override
    def get_all_areas_info(self) -> List[AreaInfo]:
        """
        Retrieve all physical areas of a study.

        Returns:
            The list of areas with their basic information.
            Note: thermals field is None for now (will be implemented later)
        """
        study_id = self.get_study_id()
        session = self.get_session()

        stmt = select(area.c.area_id, area.c.area_name).where(area.c.study_id == study_id)
        result = session.execute(stmt)

        areas_info = []
        for row in result:
            areas_info.append(AreaInfo(id=row.area_id, name=row.area_name, thermals=None))

        return areas_info

    @override
    def get_all_areas_ui_info(self) -> Dict[str, AreaUIData]:
        """
        Retrieve information about all areas' user interface (UI) from the study.

        Returns:
            A dictionary mapping area IDs to their UI data.
        """
        study_id = self.get_study_id()
        session = self.get_session()

        # Single query with JOIN to get all areas and their UI info
        stmt = (
            select(area.c.area_id, area_ui)
            .select_from(area.join(area_ui, area.c.id == area_ui.c.area_id))
            .where(area.c.study_id == study_id)
        )
        rows = session.execute(stmt).fetchall()

        if not rows:
            return {}

        # Group UI rows by area_id
        ui_by_area: Dict[str, List[Any]] = {}
        for row in rows:
            area_id = row.area_id
            if area_id not in ui_by_area:
                ui_by_area[area_id] = []
            ui_by_area[area_id].append(row)

        # Build result
        result: Dict[str, AreaUIData] = {}
        for area_id, ui_rows in ui_by_area.items():
            ui_dict: Dict[str, int | str] = {}
            layer_x: Dict[str, int] = {}
            layer_y: Dict[str, int] = {}
            layer_color: Dict[str, str] = {}

            # Find layer "0" (default layer)
            default_ui = next((row for row in ui_rows if row.layer_id == "0"), None)

            if default_ui:
                ui_dict = {
                    "x": default_ui.x,
                    "y": default_ui.y,
                    "color_r": default_ui.color_r,
                    "color_g": default_ui.color_g,
                    "color_b": default_ui.color_b,
                    "layers": " ".join(sorted([row.layer_id for row in ui_rows if row.layer_id != "0"])),
                }

            # Build layer-specific data
            for ui_row in ui_rows:
                layer_x[ui_row.layer_id] = ui_row.x
                layer_y[ui_row.layer_id] = ui_row.y
                layer_color[ui_row.layer_id] = f"{ui_row.color_r}, {ui_row.color_g}, {ui_row.color_b}"

            result[area_id] = AreaUIData(ui=ui_dict, layer_x=layer_x, layer_y=layer_y, layer_color=layer_color)

        return result

    @override
    def get_area_ui(self, area_id: str, layer: str = "0") -> AreaUI:
        """
        Retrieve UI information for a specific area and layer.

        Args:
            area_id: The area identifier.
            layer: The layer identifier (typically "0", "1", etc.). Defaults to "0".

        Returns:
            The UI properties for the area (x, y, color_rgb).

        Raises:
            AreaNotFound: If the area does not exist.
        """
        study_id = self.get_study_id()
        session = self.get_session()

        # First, get the area database ID
        stmt_area = select(area.c.id).where((area.c.study_id == study_id) & (area.c.area_id == area_id))
        area_result = session.execute(stmt_area).fetchone()

        if not area_result:
            raise AreaNotFound(area_id)

        area_db_id = area_result.id

        # Get UI for the specified layer
        stmt_ui = select(area_ui).where((area_ui.c.area_id == area_db_id) & (area_ui.c.layer_id == layer))
        ui_row = session.execute(stmt_ui).fetchone()

        if ui_row:
            return AreaUI(x=ui_row.x, y=ui_row.y, color_rgb=(ui_row.color_r, ui_row.color_g, ui_row.color_b))

        # If layer not found, fall back to layer "0"
        if layer != "0":
            stmt_ui_default = select(area_ui).where((area_ui.c.area_id == area_db_id) & (area_ui.c.layer_id == "0"))
            ui_row_default = session.execute(stmt_ui_default).fetchone()

            if ui_row_default:
                return AreaUI(
                    x=ui_row_default.x,
                    y=ui_row_default.y,
                    color_rgb=(ui_row_default.color_r, ui_row_default.color_g, ui_row_default.color_b),
                )

        # If no UI found at all, return defaults
        return AreaUI()

    @override
    def save_area(self, area_name: str) -> None:
        """
        Create a new area in the study.

        Args:
            area_name: The name of the area to create.

        Raises:
            ValueError: If the area already exists.
        """
        study_id = self.get_study_id()
        session = self.get_session()

        area_id = transform_name_to_id(area_name)

        # Check if area already exists
        stmt_check = select(area.c.id).where((area.c.study_id == study_id) & (area.c.area_id == area_id))
        existing = session.execute(stmt_check).fetchone()

        if existing:
            raise ValueError(f"Area '{area_name}' already exists and could not be created")

        # Insert new area and get the generated ID
        stmt_area = insert(area).values(study_id=study_id, area_id=area_id, area_name=area_name).returning(area.c.id)
        new_area_id = session.execute(stmt_area).scalar_one()

        # Create default UI for layer "0" using model defaults
        default_ui = AreaUI()
        r, g, b = default_ui.color_rgb
        stmt_ui = insert(area_ui).values(
            area_id=new_area_id,
            layer_id="0",
            x=default_ui.x,
            y=default_ui.y,
            color_r=r,
            color_g=g,
            color_b=b,
        )
        session.execute(stmt_ui)
        session.commit()

    @override
    def delete_area(self, area_id: str) -> None:
        """
        Delete an area from the study.

        Args:
            area_id: The area identifier to delete.

        Raises:
            AreaNotFound: If the area does not exist.
        """
        study_id = self.get_study_id()
        session = self.get_session()

        # Check if area exists
        stmt_check = select(area.c.id).where((area.c.study_id == study_id) & (area.c.area_id == area_id))
        existing = session.execute(stmt_check).fetchone()

        if not existing:
            raise AreaNotFound(area_id)

        # Delete area (cascade will delete area_ui automatically)
        stmt = delete(area).where((area.c.study_id == study_id) & (area.c.area_id == area_id))
        session.execute(stmt)
        session.commit()

    @override
    def save_area_ui(self, area_id: str, layer: str, area_ui_data: AreaUI) -> None:
        """
        Save an area's UI properties (position and color) for a specific layer.

        Args:
            area_id: The area identifier.
            layer: The layer identifier (typically "0", "1", etc.).
            area_ui_data: The UI properties to save (x, y, color_rgb).

        Raises:
            AreaNotFound: If the area does not exist.
        """
        study_id = self.get_study_id()
        session = self.get_session()

        # Get the area database ID
        stmt_area = select(area.c.id).where((area.c.study_id == study_id) & (area.c.area_id == area_id))
        area_result = session.execute(stmt_area).fetchone()

        if not area_result:
            raise AreaNotFound(area_id)

        area_db_id = area_result.id
        r, g, b = area_ui_data.color_rgb

        # Check if UI for this layer already exists
        stmt_check = select(area_ui.c.id).where((area_ui.c.area_id == area_db_id) & (area_ui.c.layer_id == layer))
        existing_ui = session.execute(stmt_check).fetchone()

        if existing_ui:
            # Update existing UI
            stmt_update = (
                update(area_ui)
                .where((area_ui.c.area_id == area_db_id) & (area_ui.c.layer_id == layer))
                .values(x=area_ui_data.x, y=area_ui_data.y, color_r=r, color_g=g, color_b=b)
            )
            session.execute(stmt_update)
        else:
            # Insert new UI
            stmt_insert = insert(area_ui).values(
                area_id=area_db_id,
                layer_id=layer,
                x=area_ui_data.x,
                y=area_ui_data.y,
                color_r=r,
                color_g=g,
                color_b=b,
            )
            session.execute(stmt_insert)
        session.commit()

    @override
    def save_layer_areas(self, layer_id: str, area_ids: List[str]) -> None:
        """
        Update the areas associated with a specific layer.

        Args:
            layer_id: The layer identifier.
            area_ids: List of area identifiers to associate with the layer.
                     Areas not in this list will be removed from the layer.

        Raises:
            LayerNotFound: If the layer does not exist.

        Note: This implementation is simplified for now. Layer existence check
              and full layer management will be implemented when layers are migrated to database.
        """
        study_id = self.get_study_id()
        session = self.get_session()

        # Get all areas for this study
        stmt_areas = select(area.c.id, area.c.area_id).where(area.c.study_id == study_id)
        all_areas = {row.area_id: row.id for row in session.execute(stmt_areas).fetchall()}

        # Get current areas in this study that have this layer
        stmt_existing = (
            select(area_ui.c.area_id)
            .select_from(area_ui.join(area, area_ui.c.area_id == area.c.id))
            .where((area_ui.c.layer_id == layer_id) & (area.c.study_id == study_id))
        )
        existing_area_db_ids = {row.area_id for row in session.execute(stmt_existing).fetchall()}

        # Map area_ids to database IDs
        target_area_db_ids = {all_areas[aid] for aid in area_ids if aid in all_areas}

        # Remove layer from areas not in the target list
        to_remove = existing_area_db_ids - target_area_db_ids
        if to_remove:
            study_scoped_area_ids = select(area.c.id).where((area.c.study_id == study_id) & (area.c.id.in_(to_remove)))
            stmt_delete = delete(area_ui).where(
                (area_ui.c.area_id.in_(study_scoped_area_ids)) & (area_ui.c.layer_id == layer_id)
            )
            session.execute(stmt_delete)

        # Add layer to areas that don't have it yet
        to_add = target_area_db_ids - existing_area_db_ids
        for area_db_id in to_add:
            # Get default UI from layer "0" to copy position
            stmt_default = select(area_ui).where((area_ui.c.area_id == area_db_id) & (area_ui.c.layer_id == "0"))
            default_ui = session.execute(stmt_default).fetchone()

            if default_ui:
                stmt_insert = insert(area_ui).values(
                    area_id=area_db_id,
                    layer_id=layer_id,
                    x=default_ui.x,
                    y=default_ui.y,
                    color_r=default_ui.color_r,
                    color_g=default_ui.color_g,
                    color_b=default_ui.color_b,
                )
                session.execute(stmt_insert)
        session.commit()
