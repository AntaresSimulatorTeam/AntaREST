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
Database implementation of AreaDao using SQLAlchemy Core.

This module provides database-backed storage for areas when storage_mode=DATABASE.
"""

import json
from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List

import polars as pl
from sqlalchemy import case, delete, insert, select, update
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.core.exceptions import AreaNotFound
from antarest.study.business.model.area_model import DEFAULT_LAYER_ID, AreaInfo, AreaUI, AreaUIData
from antarest.study.business.model.area_properties_model import AreaProperties
from antarest.study.dao.api.area_dao import AreaDao
from antarest.study.dao.database.common import area_exists, serialize_frequency_filters, validate_area_exists
from antarest.study.dao.database.models import AREA_TABLE, AREA_UI_TABLE, DISTRICT_TABLE
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id

if TYPE_CHECKING:
    from antarest.study.dao.database.database_study_dao import DatabaseStudyDao


class DatabaseAreaDao(AreaDao):
    """Database implementation of AreaDao"""

    def __init__(self, study_id: str, db_session: Session) -> None:
        """
        Initialize DatabaseAreaDao with dependencies.

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
    def get_all_area_ids(self) -> list[str]:
        """
        Retrieve all physical areas of a study.
        """
        study_id = self.get_study_id()
        session = self.get_session()

        stmt = select(AREA_TABLE.c.area_id).where(AREA_TABLE.c.study_id == study_id)
        result = session.execute(stmt)

        return [row.area_id for row in result]

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

        stmt = select(AREA_TABLE.c.area_id, AREA_TABLE.c.area_name).where(AREA_TABLE.c.study_id == study_id)
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

        # Single query to get all areas and their UI info
        stmt = select(AREA_UI_TABLE).where(AREA_UI_TABLE.c.study_id == study_id)
        rows = session.execute(stmt)

        # Group UI rows by area_id
        ui_by_area: Dict[str, List[Any]] = {}
        for row in rows:
            area_id = row.area_id
            ui_by_area.setdefault(area_id, []).append(row)

        # Build result
        result: Dict[str, AreaUIData] = {}
        for area_id, ui_rows in ui_by_area.items():
            ui_dict: Dict[str, int | str] = {}
            layer_x: Dict[str, int] = {}
            layer_y: Dict[str, int] = {}
            layer_color: Dict[str, str] = {}

            # Find default layer
            default_ui = next((row for row in ui_rows if row.layer_id == DEFAULT_LAYER_ID), None)

            if default_ui:
                ui_dict = {
                    "x": default_ui.x,
                    "y": default_ui.y,
                    "color_r": default_ui.color_r,
                    "color_g": default_ui.color_g,
                    "color_b": default_ui.color_b,
                    "layers": " ".join(sorted([row.layer_id for row in ui_rows if row.layer_id != DEFAULT_LAYER_ID])),
                }

            # Build layer-specific data
            for ui_row in ui_rows:
                layer_x[ui_row.layer_id] = ui_row.x
                layer_y[ui_row.layer_id] = ui_row.y
                layer_color[ui_row.layer_id] = f"{ui_row.color_r}, {ui_row.color_g}, {ui_row.color_b}"

            result[area_id] = AreaUIData(ui=ui_dict, layer_x=layer_x, layer_y=layer_y, layer_color=layer_color)

        return result

    @override
    def get_area_ui(self, area_id: str, layer: str = DEFAULT_LAYER_ID) -> AreaUI:
        """
        Retrieve UI information for a specific area and layer.

        Args:
            area_id: The area identifier.
            layer: The layer identifier (typically "0", "1", etc.). Defaults to DEFAULT_LAYER_ID.

        Returns:
            The UI properties for the area (x, y, color_rgb).

        Raises:
            AreaNotFound: If the area does not exist.
        """
        study_id = self.get_study_id()
        session = self.get_session()

        # Fetch both specified layer and default layer in one query
        layers_to_fetch = [layer, DEFAULT_LAYER_ID] if layer != DEFAULT_LAYER_ID else [DEFAULT_LAYER_ID]

        stmt = select(AREA_UI_TABLE).where(
            (AREA_UI_TABLE.c.study_id == study_id)
            & (AREA_UI_TABLE.c.area_id == area_id)
            & (AREA_UI_TABLE.c.layer_id.in_(layers_to_fetch))
        )
        rows = {row.layer_id: row for row in session.execute(stmt)}

        # If no UI found, check if area exists (to raise proper error)
        if not rows:
            validate_area_exists(session, study_id, area_id)
            return AreaUI()

        # Prefer specified layer, fall back to default
        ui_row = rows.get(layer) or rows.get(DEFAULT_LAYER_ID)

        if ui_row:
            return AreaUI(x=ui_row.x, y=ui_row.y, color_rgb=(ui_row.color_r, ui_row.color_g, ui_row.color_b))

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

        if area_exists(session, study_id, area_id):
            raise ValueError(f"Area '{area_name}' already exists and could not be created")

        # Insert new area
        area_properties = AreaProperties()
        stmt_area = insert(AREA_TABLE).values(
            study_id=study_id,
            area_id=area_id,
            area_name=area_name,
            energy_cost_unsupplied=area_properties.energy_cost_unsupplied,
            energy_cost_spilled=area_properties.energy_cost_spilled,
            non_dispatch_power=area_properties.non_dispatch_power,
            dispatch_hydro_power=area_properties.dispatch_hydro_power,
            other_dispatch_power=area_properties.other_dispatch_power,
            spread_unsupplied_energy_cost=area_properties.spread_unsupplied_energy_cost,
            spread_spilled_energy_cost=area_properties.spread_spilled_energy_cost,
            filter_synthesis=serialize_frequency_filters(area_properties.filter_synthesis),
            filter_by_year=serialize_frequency_filters(area_properties.filter_by_year),
            adequacy_patch_mode=area_properties.adequacy_patch_mode,
        )
        session.execute(stmt_area)

        # The commit is handled inside the next method.
        self._create_new_ui(area_id, DEFAULT_LAYER_ID, AreaUI())

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

        validate_area_exists(session, study_id, area_id)

        # Remove area from districts that reference it
        stmt = select(DISTRICT_TABLE).where(DISTRICT_TABLE.c.study_id == study_id)
        district_rows = session.execute(stmt).fetchall()

        for row in district_rows:
            add_areas = set(json.loads(row.add_areas))
            subtract_areas = set(json.loads(row.subtract_areas))

            if area_id in add_areas or area_id in subtract_areas:
                add_areas.discard(area_id)
                subtract_areas.discard(area_id)

                session.execute(
                    update(DISTRICT_TABLE)
                    .where((DISTRICT_TABLE.c.study_id == study_id) & (DISTRICT_TABLE.c.district_id == row.district_id))
                    .values(
                        add_areas=json.dumps(list(add_areas)),
                        subtract_areas=json.dumps(list(subtract_areas)),
                    )
                )

        # Delete area
        delete_stmt = delete(AREA_TABLE).where((AREA_TABLE.c.study_id == study_id) & (AREA_TABLE.c.area_id == area_id))
        session.execute(delete_stmt)
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

        validate_area_exists(session, study_id, area_id)

        r, g, b = area_ui_data.color_rgb

        # Check if UI for this layer already exists
        stmt_check = select(AREA_UI_TABLE.c.layer_id).where(
            (AREA_UI_TABLE.c.study_id == study_id)
            & (AREA_UI_TABLE.c.area_id == area_id)
            & (AREA_UI_TABLE.c.layer_id == layer)
        )
        existing_ui = session.execute(stmt_check).fetchone()

        if existing_ui:
            # Update existing UI
            stmt_update = (
                update(AREA_UI_TABLE)
                .where(
                    (AREA_UI_TABLE.c.study_id == study_id)
                    & (AREA_UI_TABLE.c.area_id == area_id)
                    & (AREA_UI_TABLE.c.layer_id == layer)
                )
                .values(x=area_ui_data.x, y=area_ui_data.y, color_r=r, color_g=g, color_b=b)
            )
            session.execute(stmt_update)
            session.commit()
        else:
            self._create_new_ui(area_id, layer, area_ui_data)

    @override
    def get_invalid_area_ids(self, areas: list[str]) -> list[str]:
        """
        Check all areas exists in the study.
        """
        areas_set = set(areas)
        all_areas = set(self.get_all_area_ids())
        invalid_areas = areas_set - all_areas
        return list(invalid_areas)

    @override
    def save_layer_areas(self, layer_id: str, area_ids: List[str]) -> None:
        """
        Update the areas associated with a specific layer.

        Args:
            layer_id: The layer identifier.
            area_ids: List of area identifiers to associate with the layer.
                     Areas not in this list will be removed from the layer.

        Raises:
            AreaNotFound: If any area_id does not exist.
        """
        study_id = self.get_study_id()
        session = self.get_session()

        # Get all areas and which ones already have this layer
        stmt = (
            select(
                AREA_TABLE.c.area_id,
                case((AREA_UI_TABLE.c.area_id.isnot(None), True), else_=False).label("has_layer"),
            )
            .select_from(
                AREA_TABLE.outerjoin(
                    AREA_UI_TABLE,
                    (AREA_TABLE.c.area_id == AREA_UI_TABLE.c.area_id)
                    & (AREA_UI_TABLE.c.study_id == study_id)
                    & (AREA_UI_TABLE.c.layer_id == layer_id),
                )
            )
            .where(AREA_TABLE.c.study_id == study_id)
        )

        all_area_ids = set()
        areas_with_layer = set()
        for row in session.execute(stmt):
            all_area_ids.add(row.area_id)
            if row.has_layer:
                areas_with_layer.add(row.area_id)

        # Check for invalid area_ids
        target_area_ids = set(area_ids)
        invalid_ids = target_area_ids - all_area_ids
        if invalid_ids:
            raise AreaNotFound(*invalid_ids)

        # Remove layer from areas not in the target list
        to_remove = areas_with_layer - target_area_ids
        if to_remove:
            stmt_delete = delete(AREA_UI_TABLE).where(
                (AREA_UI_TABLE.c.study_id == study_id)
                & (AREA_UI_TABLE.c.area_id.in_(to_remove))
                & (AREA_UI_TABLE.c.layer_id == layer_id)
            )
            session.execute(stmt_delete)

        # Add layer to areas that don't have it yet (batch operation to avoid N+1 queries)
        to_add = target_area_ids - areas_with_layer
        if to_add:
            # Batch fetch all default UIs for areas to add
            stmt_defaults = select(AREA_UI_TABLE).where(
                (AREA_UI_TABLE.c.study_id == study_id)
                & (AREA_UI_TABLE.c.area_id.in_(to_add))
                & (AREA_UI_TABLE.c.layer_id == DEFAULT_LAYER_ID)
            )
            default_uis = {row.area_id: row for row in session.execute(stmt_defaults).fetchall()}

            # Prepare batch insert values
            insert_values = []
            for aid in to_add:
                if aid in default_uis:
                    ui = default_uis[aid]
                    insert_values.append(
                        {
                            "study_id": study_id,
                            "area_id": aid,
                            "layer_id": layer_id,
                            "x": ui.x,
                            "y": ui.y,
                            "color_r": ui.color_r,
                            "color_g": ui.color_g,
                            "color_b": ui.color_b,
                        }
                    )

            # Execute batch insert
            if insert_values:
                session.execute(insert(AREA_UI_TABLE), insert_values)
        session.commit()

    def _create_new_ui(self, area_id: str, layer: str, area_ui: AreaUI) -> None:
        r, g, b = area_ui.color_rgb
        stmt_insert = insert(AREA_UI_TABLE).values(
            study_id=self.get_study_id(),
            area_id=area_id,
            layer_id=layer,
            x=area_ui.x,
            y=area_ui.y,
            color_r=r,
            color_g=g,
            color_b=b,
        )
        self.get_session().execute(stmt_insert)
        self.get_session().commit()

    # Time series methods - not yet implemented for database storage mode
    @override
    def get_load(self, area_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_misc_gen(self, area_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_reserves(self, area_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_solar(self, area_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_wind(self, area_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_load(self, area_id: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_misc_gen(self, area_id: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_reserves(self, area_id: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_solar(self, area_id: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_wind(self, area_id: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")
