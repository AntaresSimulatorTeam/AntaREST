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

import enum
import logging
from http import HTTPStatus
from typing import Any, Dict, List, Mapping, Optional, Sequence, cast

import typing_extensions as te
from fastapi import APIRouter, Body, Depends, Query
from starlette.responses import RedirectResponse

from antarest.core.config import Config
from antarest.core.jwt import JWTUser
from antarest.core.model import JSON, StudyPermissionType
from antarest.core.requests import RequestParameters
from antarest.core.utils.utils import sanitize_uuid
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth
from antarest.matrixstore.matrix_editor import MatrixEditInstruction
from antarest.study.business.adequacy_patch_management import AdequacyPatchFormFields
from antarest.study.business.advanced_parameters_management import AdvancedParamsFormFields
from antarest.study.business.allocation_management import AllocationField, AllocationFormFields, AllocationMatrix
from antarest.study.business.areas.hydro_management import HydroManagementOptions, InflowStructure
from antarest.study.business.areas.properties_management import PropertiesFormFields
from antarest.study.business.areas.renewable_management import RenewableManager
from antarest.study.business.areas.st_storage_management import (
    STStorageManager,
    STStorageMatrix,
    STStorageTimeSeries,
)
from antarest.study.business.areas.thermal_management import (
    ThermalClusterCreation,
    ThermalClusterInput,
    ThermalClusterOutput,
    ThermalManager,
)
from antarest.study.business.binding_constraint_management import (
    ConstraintCreation,
    ConstraintFilters,
    ConstraintInput,
    ConstraintOutput,
    ConstraintTerm,
)
from antarest.study.business.correlation_management import (
    AreaCoefficientItem,
    CorrelationFormFields,
    CorrelationMatrix,
)
from antarest.study.business.district_manager import DistrictCreationDTO, DistrictInfoDTO, DistrictUpdateDTO
from antarest.study.business.general_management import GeneralFormFields
from antarest.study.business.model.area_model import AreaCreationDTO, AreaInfoDTO, AreaType, LayerInfoDTO, UpdateAreaUi
from antarest.study.business.model.link_model import LinkBaseDTO, LinkDTO
from antarest.study.business.model.renewable_cluster_model import (
    RenewableClusterCreation,
    RenewableClusterOutput,
    RenewableClusterUpdate,
)
from antarest.study.business.model.sts_model import STStorageCreation, STStorageOutput, STStorageUpdate
from antarest.study.business.optimization_management import OptimizationFormFields
from antarest.study.business.playlist_management import PlaylistColumns
from antarest.study.business.scenario_builder_management import Rulesets, ScenarioType
from antarest.study.business.table_mode_management import TableDataDTO, TableModeType
from antarest.study.business.thematic_trimming_field_infos import ThematicTrimmingFormFields
from antarest.study.business.timeseries_config_management import TimeSeriesConfigDTO
from antarest.study.service import StudyService
from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import (
    BindingConstraintFrequency,
    BindingConstraintOperator,
)
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.ruleset_matrices import TableForm as SBTableForm

logger = logging.getLogger(__name__)


class BCKeyValueType(te.TypedDict):
    """Deprecated type for binding constraint key-value pair (used for update)"""

    key: str
    value: str | int | float | bool


class ClusterType(enum.StrEnum):
    """
    Cluster type:

    - `STORAGE`: short-term storages
    - `RENEWABLES`: renewable clusters
    - `THERMALS`: thermal clusters
    """

    ST_STORAGES = "storages"
    RENEWABLES = "renewables"
    THERMALS = "thermals"


def create_study_data_routes(study_service: StudyService, config: Config) -> APIRouter:
    """
    Endpoint implementation for studies area management

    Args:
        study_service: study service facade to handle request
        config: main server configuration

    Returns:
        The FastAPI route for Study data management
    """
    bp = APIRouter(prefix="/v1")
    auth = Auth(config)

    # noinspection PyShadowingBuiltins
    @bp.get(
        "/studies/{uuid}/areas",
        tags=[APITag.study_data],
        summary="Get all areas basic info",
        response_model=List[AreaInfoDTO] | Dict[str, Any],
    )
    def get_areas(
        uuid: str,
        type: AreaType = Query(None),
        ui: bool = False,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> List[AreaInfoDTO] | Dict[str, Any]:
        logger.info(
            f"Fetching area list (type={type}) for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        areas_list = study_service.get_all_areas(uuid, type, ui, params)
        return areas_list

    @bp.get(
        "/studies/{uuid}/links",
        tags=[APITag.study_data],
        summary="Get all links",
        response_model=List[LinkDTO],
    )
    def get_links(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> List[LinkDTO]:
        logger.info(
            f"Fetching link list for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        areas_list = study_service.get_all_links(uuid, params)
        return areas_list

    @bp.post(
        "/studies/{uuid}/areas",
        tags=[APITag.study_data],
        summary="Create a new area",
        response_model=AreaInfoDTO,
    )
    def create_area(
        uuid: str,
        area_creation_info: AreaCreationDTO,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Creating new area for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        return study_service.create_area(uuid, area_creation_info, params)

    @bp.post(
        "/studies/{uuid}/links",
        tags=[APITag.study_data],
        summary="Create a link",
        response_model=LinkDTO,
    )
    def create_link(
        uuid: str,
        link_creation_info: LinkDTO,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> LinkDTO:
        logger.info(
            f"Creating new link for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        return study_service.create_link(uuid, link_creation_info, params)

    @bp.put(
        "/studies/{uuid}/links/{area_from}/{area_to}",
        tags=[APITag.study_data],
        summary="Update a link",
        response_model=LinkDTO,
    )
    def update_link(
        uuid: str,
        area_from: str,
        area_to: str,
        link_update_dto: LinkBaseDTO,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Updating link {area_from} -> {area_to} for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        return study_service.update_link(uuid, area_from, area_to, link_update_dto, params)

    @bp.put(
        "/studies/{uuid}/areas/{area_id}/ui",
        tags=[APITag.study_data],
        summary="Update area information",
        response_model=None,
    )
    def update_area_ui(
        uuid: str,
        area_id: str,
        area_ui: UpdateAreaUi,
        layer: str = "0",
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Updating area ui {area_id} for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        return study_service.update_area_ui(uuid, area_id, area_ui, layer, params)

    @bp.delete(
        "/studies/{uuid}/areas/{area_id}",
        tags=[APITag.study_data],
        summary="Delete an area",
        response_model=str,
    )
    def delete_area(
        uuid: str,
        area_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Removing area {area_id} in study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        uuid = sanitize_uuid(uuid)
        area_id = transform_name_to_id(area_id)
        study_service.delete_area(uuid, area_id, params)
        return area_id

    @bp.delete(
        "/studies/{uuid}/links/{area_from}/{area_to}",
        tags=[APITag.study_data],
        summary="Delete a link",
        response_model=str,
    )
    def delete_link(
        uuid: str,
        area_from: str,
        area_to: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Removing link {area_from}%{area_to} in study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        area_from = transform_name_to_id(area_from)
        area_to = transform_name_to_id(area_to)
        study_service.delete_link(uuid, area_from, area_to, params)
        return f"{area_from}%{area_to}"

    @bp.get(
        "/studies/{uuid}/layers",
        tags=[APITag.study_data],
        summary="Get all layers info",
        response_model=List[LayerInfoDTO],
    )
    def get_layers(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> List[LayerInfoDTO]:
        logger.info(
            f"Fetching layer list for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ, params)
        return study_service.area_manager.get_layers(study_service.get_study_interface(study))

    @bp.post(
        "/studies/{uuid}/layers",
        tags=[APITag.study_data],
        summary="Create new layer",
        response_model=str,
    )
    def create_layer(
        uuid: str,
        name: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> str:
        logger.info(
            f"Create layer {name} for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, params)
        return study_service.area_manager.create_layer(study_service.get_study_interface(study), name)

    @bp.put(
        "/studies/{uuid}/layers/{layer_id}",
        tags=[APITag.study_data],
        summary="Update layer",
    )
    def update_layer(
        uuid: str,
        layer_id: str,
        name: str = "",
        areas: Optional[List[str]] = None,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> None:
        logger.info(
            f"Updating layer {layer_id} for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, params)
        study_interface = study_service.get_study_interface(study)
        if name:
            study_service.area_manager.update_layer_name(study_interface, layer_id, name)
        if areas:
            study_service.area_manager.update_layer_areas(study_interface, layer_id, areas)

    @bp.delete(
        "/studies/{uuid}/layers/{layer_id}",
        tags=[APITag.study_data],
        summary="Remove layer",
        status_code=HTTPStatus.NO_CONTENT,
        response_model=None,
    )
    def remove_layer(
        uuid: str,
        layer_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> None:
        logger.info(
            f"Remove layer {layer_id} for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ, params)
        study_service.area_manager.remove_layer(study_service.get_study_interface(study), layer_id)

    @bp.get(
        "/studies/{uuid}/districts",
        tags=[APITag.study_data],
        summary="Get the list of districts defined in this study",
        response_model=List[DistrictInfoDTO],
    )
    def get_districts(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> List[DistrictInfoDTO]:
        logger.info(
            f"Fetching districts list for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ, params)
        study_interface = study_service.get_study_interface(study)
        return study_service.district_manager.get_districts(study_interface)

    @bp.post(
        "/studies/{uuid}/districts",
        tags=[APITag.study_data],
        summary="Create a new district in the study",
        response_model=DistrictInfoDTO,
    )
    def create_district(
        uuid: str,
        dto: DistrictCreationDTO,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> DistrictInfoDTO:
        logger.info(
            f"Create district {dto.name} for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, params)
        study_interface = study_service.get_study_interface(study)
        return study_service.district_manager.create_district(study_interface, dto)

    @bp.put(
        "/studies/{uuid}/districts/{district_id}",
        tags=[APITag.study_data],
        summary="Update the properties of a district",
    )
    def update_district(
        uuid: str,
        district_id: str,
        dto: DistrictUpdateDTO,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> None:
        logger.info(
            f"Updating district {district_id} for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, params)
        study_interface = study_service.get_study_interface(study)
        study_service.district_manager.update_district(study_interface, district_id, dto)

    @bp.delete(
        "/studies/{uuid}/districts/{district_id}",
        tags=[APITag.study_data],
        summary="Remove a district from a study",
    )
    def remove_district(
        uuid: str,
        district_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> None:
        logger.info(
            f"Remove district {district_id} for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, params)
        study_interface = study_service.get_study_interface(study)
        study_service.district_manager.remove_district(study_interface, district_id)

    @bp.get(
        "/studies/{uuid}/areas/{area_id}/hydro/form",
        tags=[APITag.study_data],
        summary="Get Hydro config values for form",
        response_model=HydroManagementOptions,
        response_model_exclude_none=True,
    )
    def get_hydro_form_values(
        uuid: str,
        area_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> HydroManagementOptions:
        logger.info(
            msg=f"Getting Hydro management config for area {area_id} of study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ, params)
        study_interface = study_service.get_study_interface(study)
        return study_service.hydro_manager.get_hydro_management_options(study_interface, area_id)

    @bp.put(
        "/studies/{uuid}/areas/{area_id}/hydro/form",
        tags=[APITag.study_data],
        summary="Set Hydro config with values from form",
    )
    def set_hydro_form_values(
        uuid: str,
        area_id: str,
        data: HydroManagementOptions,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            msg=f"Updating Hydro management config for area {area_id} of study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, params)
        study_interface = study_service.get_study_interface(study)
        study_service.hydro_manager.update_hydro_management_options(study_interface, data, area_id)

    # noinspection SpellCheckingInspection
    @bp.get(
        "/studies/{uuid}/areas/{area_id}/hydro/inflow-structure",
        tags=[APITag.study_data],
        summary="Get inflow structure values",
        response_model=InflowStructure,
    )
    def get_inflow_structure(
        uuid: str,
        area_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> InflowStructure:
        """Get the configuration for the hydraulic inflow structure of the given area."""
        logger.info(
            msg=f"Getting inflow structure values for area {area_id} of study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ, params)
        study_interface = study_service.get_study_interface(study)
        return study_service.hydro_manager.get_inflow_structure(study_interface, area_id)

    @bp.put(
        "/studies/{uuid}/areas/{area_id}/hydro/inflow-structure",
        tags=[APITag.study_data],
        summary="Update inflow structure values",
    )
    def update_inflow_structure(
        uuid: str,
        area_id: str,
        values: InflowStructure,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> None:
        """Update the configuration for the hydraulic inflow structure of the given area."""
        logger.info(
            msg=f"Updating inflow structure values for area {area_id} of study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, params)
        study_interface = study_service.get_study_interface(study)
        study_service.hydro_manager.update_inflow_structure(study_interface, area_id, values)

    @bp.put(
        "/studies/{uuid}/matrix",
        tags=[APITag.study_data],
        summary="Edit matrix",
    )
    def edit_matrix(
        uuid: str,
        path: str,
        matrix_edit_instructions: List[MatrixEditInstruction] = Body(...),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        # NOTE: This Markdown documentation is reflected in the Swagger API
        """
        Edit a matrix in a study based on the provided edit instructions.

        Args:
        - `uuid`: The UUID of the study.
        - `path`: the path of the matrix to update.
        - `matrix_edit_instructions`: a list of edit instructions to be applied to the matrix.

        Permissions:
        - User must have WRITE permission on the study.
        """
        params = RequestParameters(user=current_user)
        study_service.update_matrix(uuid, path, matrix_edit_instructions, params)

    @bp.get(
        "/studies/{uuid}/config/thematictrimming/form",
        tags=[APITag.study_data],
        summary="Get thematic trimming config",
        response_model=ThematicTrimmingFormFields,
        response_model_exclude_none=True,
    )
    def get_thematic_trimming(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> ThematicTrimmingFormFields:
        logger.info(
            f"Fetching thematic trimming config for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ, params)
        study_interface = study_service.get_study_interface(study)
        return study_service.thematic_trimming_manager.get_field_values(study_interface)

    @bp.put(
        path="/studies/{uuid}/config/thematictrimming/form",
        tags=[APITag.study_data],
        summary="Set thematic trimming config",
    )
    def set_thematic_trimming(
        uuid: str,
        field_values: ThematicTrimmingFormFields,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> None:
        logger.info(
            f"Updating thematic trimming config for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, params)
        study_interface = study_service.get_study_interface(study)
        study_service.thematic_trimming_manager.set_field_values(study_interface, field_values)

    @bp.get(
        path="/studies/{uuid}/config/playlist/form",
        tags=[APITag.study_data],
        summary="Get MC Scenario playlist data for table form",
        response_model=Dict[int, PlaylistColumns],
        response_model_exclude_none=True,
    )
    def get_playlist(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Dict[int, PlaylistColumns]:
        logger.info(
            f"Getting MC Scenario playlist data for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ, params)
        study_interface = study_service.get_study_interface(study)
        return study_service.playlist_manager.get_table_data(study_interface)

    @bp.put(
        path="/studies/{uuid}/config/playlist/form",
        tags=[APITag.study_data],
        summary="Set MC Scenario playlist data with values from table form",
    )
    def set_playlist(
        uuid: str,
        data: Dict[int, PlaylistColumns],
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> None:
        logger.info(
            f"Updating MC Scenario playlist table data for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, params)
        study_interface = study_service.get_study_interface(study)
        study_service.playlist_manager.set_table_data(study_interface, data)

    @bp.get(
        "/studies/{uuid}/config/playlist",
        tags=[APITag.study_data],
        summary="Get playlist config",
        response_model=Optional[Dict[int, float]],
    )
    def get_playlist_config(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Optional[Dict[int, float]]:
        logger.info(
            f"Fetching playlist config for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ, params)
        study_interface = study_service.get_study_interface(study)
        return study_service.config_manager.get_playlist(study_interface)

    @bp.put(
        path="/studies/{uuid}/config/playlist",
        tags=[APITag.study_data],
        summary="Set playlist config",
    )
    def set_playlist_config(
        uuid: str,
        active: bool = True,
        reverse: bool = False,
        playlist: Optional[List[int]] = Body(default=None),
        weights: Optional[Dict[int, int]] = Body(default=None),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Updating playlist config for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, params)
        study_interface = study_service.get_study_interface(study)
        study_service.config_manager.set_playlist(study_interface, playlist, weights, reverse, active)

    @bp.get(
        path="/studies/{uuid}/config/scenariobuilder",
        tags=[APITag.study_data],
        summary="Get MC Scenario builder config",
        response_model=Rulesets,
    )
    def get_scenario_builder_config(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Rulesets:
        logger.info(
            f"Getting MC Scenario builder config for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ, params)
        study_interface = study_service.get_study_interface(study)
        return study_service.scenario_builder_manager.get_config(study_interface)

    @bp.get(
        path="/studies/{uuid}/config/scenariobuilder/{scenario_type}",
        tags=[APITag.study_data],
        summary="Get MC Scenario builder config",
        response_model=Dict[str, SBTableForm],
    )
    def get_scenario_builder_config_by_type(
        uuid: str,
        scenario_type: ScenarioType,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Dict[str, SBTableForm]:
        """
        Retrieve the scenario matrix corresponding to a specified scenario type.

        The returned scenario matrix is structured as follows:

        ```json
        {
            "scenario_type": {
                "area_id": {
                    "year": <TS number>,
                    ...
                },
                ...
            },
        }
        ```

        For thermal and renewable scenarios, the format is:

        ```json
        {
            "scenario_type": {
                "area_id": {
                    "cluster_id": {
                        "year": <TS number>,
                        ...
                    },
                    ...
                },
                ...
            },
        }
        ```

        For hydraulic levels scenarios, the format is:

        ```json
        {
            "scenario_type": {
                "area_id": {
                    "year": <Percent 0-100>,
                    ...
                },
                ...
            },
        }
        ```

        For binding constraints scenarios, the format is:

        ```json
        {
            "scenario_type": {
                "group_name": {
                    "year": <TS number>,
                    ...
                },
                ...
            },
        }
        ```
        """
        logger.info(
            f"Getting MC Scenario builder config for study {uuid} with scenario type filter: {scenario_type}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ, params)
        study_interface = study_service.get_study_interface(study)
        table_form = study_service.scenario_builder_manager.get_scenario_by_type(study_interface, scenario_type)
        return {scenario_type: table_form}

    @bp.put(
        path="/studies/{uuid}/config/scenariobuilder",
        tags=[APITag.study_data],
        summary="Set MC Scenario builder config",
    )
    def update_scenario_builder_config(
        uuid: str,
        data: Rulesets,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> None:
        logger.info(
            f"Updating MC Scenario builder config for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, params)
        study_interface = study_service.get_study_interface(study)
        study_service.scenario_builder_manager.update_config(study_interface, data)

    @bp.put(
        path="/studies/{uuid}/config/scenariobuilder/{scenario_type}",
        tags=[APITag.study_data],
        summary="Set MC Scenario builder config",
        response_model=Dict[str, SBTableForm],
    )
    def update_scenario_builder_config_by_type(
        uuid: str,
        scenario_type: ScenarioType,
        data: Dict[str, SBTableForm],
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Dict[str, SBTableForm]:
        """
        Update the scenario matrix corresponding to a specified scenario type.

        Args:
        - `data`: partial scenario matrix using the following structure:

          ```json
          {
              "scenario_type": {
                  "area_id": {
                      "year": <TS number>,
                      ...
                  },
                  ...
              },
          }
          ```

          > See the GET endpoint for the structure of the scenario matrix.

        Returns:
        - The updated scenario matrix.
        """
        logger.info(
            f"Updating MC Scenario builder config for study {uuid} with scenario type filter: {scenario_type}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, params)
        study_interface = study_service.get_study_interface(study)
        table_form = data[scenario_type]
        table_form = study_service.scenario_builder_manager.update_scenario_by_type(
            study_interface, table_form, scenario_type
        )
        return {scenario_type: table_form}

    @bp.get(
        path="/studies/{uuid}/config/general/form",
        tags=[APITag.study_data],
        summary="Get General config values for form",
        response_model=GeneralFormFields,
        response_model_exclude_none=True,
    )
    def get_general_form_values(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> GeneralFormFields:
        logger.info(
            msg=f"Getting General management config for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ, params)
        study_interface = study_service.get_study_interface(study)
        return study_service.general_manager.get_field_values(study_interface)

    @bp.put(
        path="/studies/{uuid}/config/general/form",
        tags=[APITag.study_data],
        summary="Set General config with values from form",
    )
    def set_general_form_values(
        uuid: str,
        field_values: GeneralFormFields,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> None:
        logger.info(
            f"Updating General management config for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, params)
        study_interface = study_service.get_study_interface(study)
        study_service.general_manager.set_field_values(study_interface, field_values)

    @bp.get(
        path="/studies/{uuid}/config/optimization/form",
        tags=[APITag.study_data],
        summary="Get optimization config values for form",
        response_model=OptimizationFormFields,
        response_model_exclude_none=True,
    )
    def get_optimization_form_values(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> OptimizationFormFields:
        logger.info(
            msg=f"Getting optimization config for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ, params)
        study_interface = study_service.get_study_interface(study)
        return study_service.optimization_manager.get_field_values(study_interface)

    @bp.put(
        path="/studies/{uuid}/config/optimization/form",
        tags=[APITag.study_data],
        summary="Set optimization config with values from form",
    )
    def set_optimization_form_values(
        uuid: str,
        field_values: OptimizationFormFields,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> None:
        logger.info(
            f"Updating optimization config for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, params)
        study_interface = study_service.get_study_interface(study)
        study_service.optimization_manager.set_field_values(study_interface, field_values)

    @bp.get(
        path="/studies/{uuid}/config/adequacypatch/form",
        tags=[APITag.study_data],
        summary="Get adequacy patch config values for form",
        response_model=AdequacyPatchFormFields,
        response_model_exclude_none=True,
    )
    def get_adequacy_patch_form_values(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> AdequacyPatchFormFields:
        logger.info(
            msg=f"Getting adequacy patch config for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ, params)
        study_interface = study_service.get_study_interface(study)
        return study_service.adequacy_patch_manager.get_field_values(study_interface)

    @bp.put(
        path="/studies/{uuid}/config/adequacypatch/form",
        tags=[APITag.study_data],
        summary="Set adequacy patch config with values from form",
    )
    def set_adequacy_patch_form_values(
        uuid: str,
        field_values: AdequacyPatchFormFields,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> None:
        logger.info(
            f"Updating adequacy patch config for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, params)
        study_interface = study_service.get_study_interface(study)
        study_service.adequacy_patch_manager.set_field_values(study_interface, field_values)

    @bp.get(
        path="/studies/{uuid}/timeseries/config",
        tags=[APITag.study_data],
        summary="Gets the TS Generation config",
        response_model=TimeSeriesConfigDTO,
        response_model_exclude_none=True,
    )
    def get_timeseries_form_values(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> TimeSeriesConfigDTO:
        logger.info(
            msg=f"Getting Time-Series generation config for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ, params)
        study_interface = study_service.get_study_interface(study)
        return study_service.ts_config_manager.get_values(study_interface)

    @bp.put(
        path="/studies/{uuid}/timeseries/config",
        tags=[APITag.study_data],
        summary="Sets the TS Generation config",
    )
    def set_ts_generation_config(
        uuid: str, field_values: TimeSeriesConfigDTO, current_user: JWTUser = Depends(auth.get_current_user)
    ) -> None:
        logger.info(
            f"Updating Time-Series generation config for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, params)
        study_interface = study_service.get_study_interface(study)
        study_service.ts_config_manager.set_values(study_interface, field_values)

    @bp.get(
        path="/table-schema/{table_type}",
        tags=[APITag.study_data],
        summary="Get table schema",
    )
    def get_table_schema(
        table_type: TableModeType,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> JSON:
        """
        Get the properties of the table columns.

        Args:
        - `table_type`: The type of table to get the schema for.
        """
        logger.info("Getting table schema", extra={"user": current_user.id})
        model_schema = study_service.table_mode_manager.get_table_schema(table_type)
        return model_schema

    @bp.get(
        path="/studies/{uuid}/table-mode/{table_type}",
        tags=[APITag.study_data],
        summary="Get table data for table form",
    )
    def get_table_mode(
        uuid: str,
        table_type: TableModeType,
        columns: str = Query("", description="A comma-separated list of columns to include in the table data"),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> TableDataDTO:
        """
        Get the table data for the given study and table type.

        Args:
        - uuid: The UUID of the study.
        - table_type: The type of table to get the data for.
        """
        logger.info(
            f"Getting table data for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ, params)
        study_interface = study_service.get_study_interface(study)
        column_list = columns.split(",") if columns else []
        table_data = study_service.table_mode_manager.get_table_data(study_interface, table_type, column_list)
        return table_data

    @bp.put(
        path="/studies/{uuid}/table-mode/{table_type}",
        tags=[APITag.study_data],
        summary="Update table data with values from table form",
    )
    def update_table_mode(
        uuid: str,
        table_type: TableModeType,
        data: TableDataDTO = Body(
            ...,
            example={
                "de / nuclear_cl1": {
                    "enabled": True,
                    "group": "Nuclear",
                    "unitCount": 17,
                    "nominalCapacity": 123,
                },
                "de / gas_cl1": {
                    "enabled": True,
                    "group": "Gas",
                    "unitCount": 15,
                    "nominalCapacity": 456,
                },
            },
        ),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> TableDataDTO:
        """
        Update the table data for the given study and table type.

        Args:
        - uuid: The UUID of the study.
        - table_type: The type of table to update.
        - data: The table data to update.
        """
        logger.info(
            f"Updating table data for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, params)
        study_interface = study_service.get_study_interface(study)
        table_data = study_service.table_mode_manager.update_table_data(study_interface, table_type, data)
        return table_data

    @bp.post(
        "/studies/_update_version",
        tags=[APITag.study_data],
        summary="update database version of all studies",
    )
    def update_version(
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        params = RequestParameters(user=current_user)
        study_service.check_and_update_all_study_versions_in_database(params)

    @bp.get(
        "/studies/{uuid}/bindingconstraints",
        tags=[APITag.study_data],
        summary="Get binding constraint list",
        response_model=List[ConstraintOutput],
    )
    def get_binding_constraint_list(
        uuid: str,
        enabled: Optional[bool] = Query(None, description="Filter results based on enabled status"),
        operator: BindingConstraintOperator = Query(None, description="Filter results based on operator"),
        comments: str = Query("", description="Filter results based on comments (word match)"),
        group: str = Query("", description="filter binding constraints based on group name (exact match)"),
        time_step: BindingConstraintFrequency = Query(
            None,
            description="Filter results based on time step",
            alias="timeStep",
        ),
        area_name: str = Query(
            "",
            description="Filter results based on area name (word match)",
            alias="areaName",
        ),
        cluster_name: str = Query(
            "",
            description="Filter results based on cluster name (word match)",
            alias="clusterName",
        ),
        link_id: str = Query(
            "",
            description="Filter results based on link ID ('area1%area2')",
            alias="linkId",
        ),
        cluster_id: str = Query(
            "",
            description="Filter results based on cluster ID ('area.cluster')",
            alias="clusterId",
        ),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Sequence[ConstraintOutput]:
        logger.info(
            f"Fetching binding constraint list for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ, params)
        study_interface = study_service.get_study_interface(study)
        filters = ConstraintFilters(
            enabled=enabled,
            operator=operator,
            comments=comments,
            group=group,
            time_step=time_step,
            area_name=area_name,
            cluster_name=cluster_name,
            link_id=link_id,
            cluster_id=cluster_id,
        )
        return study_service.binding_constraint_manager.get_binding_constraints(study_interface, filters)

    @bp.get(
        "/studies/{uuid}/bindingconstraints/{binding_constraint_id}",
        tags=[APITag.study_data],
        summary="Get binding constraint",
        response_model=ConstraintOutput,  # TODO: redundant ?
    )
    def get_binding_constraint(
        uuid: str,
        binding_constraint_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> ConstraintOutput:
        logger.info(
            f"Fetching binding constraint {binding_constraint_id} for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ, params)
        study_interface = study_service.get_study_interface(study)
        return study_service.binding_constraint_manager.get_binding_constraint(study_interface, binding_constraint_id)

    @bp.put(
        "/studies/{uuid}/bindingconstraints/{binding_constraint_id}",
        tags=[APITag.study_data],
        summary="Update binding constraint",
    )
    def update_binding_constraint(
        uuid: str,
        binding_constraint_id: str,
        data: ConstraintInput,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> ConstraintOutput:
        logger.info(
            f"Update binding constraint {binding_constraint_id} for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, params)
        study_interface = study_service.get_study_interface(study)
        return study_service.binding_constraint_manager.update_binding_constraint(
            study_interface, binding_constraint_id, data
        )

    @bp.get(
        "/studies/{uuid}/constraint-groups",
        tags=[APITag.study_data],
        summary="Get the list of binding constraint groups",
    )
    def get_grouped_constraints(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Mapping[str, Sequence[ConstraintOutput]]:
        """
        Get the list of binding constraint groups for the study.

        Args:
        - `uuid`: The UUID of the study.

        Returns:
        - The list of binding constraints for each group.
        """
        logger.info(
            f"Fetching binding constraint groups for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ, params)
        study_interface = study_service.get_study_interface(study)
        result = study_service.binding_constraint_manager.get_grouped_constraints(study_interface)
        return result

    @bp.get(
        # We use "validate-all" because it is unlikely to conflict with a group name.
        "/studies/{uuid}/constraint-groups/validate-all",
        tags=[APITag.study_data],
        summary="Validate all binding constraint groups",
        response_model=None,
    )
    def validate_constraint_groups(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> bool:
        """
        Checks if the dimensions of the right-hand side matrices are consistent with
        the dimensions of the binding constraint matrices within the same group.

        Args:
        - `uuid`: The study UUID.

        Returns:
        - `true` if all groups are valid.

        Raises:
        - HTTPException(422) if any group is invalid.
        """
        logger.info(
            f"Validating all binding constraint groups for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ, params)
        study_interface = study_service.get_study_interface(study)
        return study_service.binding_constraint_manager.validate_constraint_groups(study_interface)

    @bp.get(
        "/studies/{uuid}/constraint-groups/{group}",
        tags=[APITag.study_data],
        summary="Get the binding constraint group",
    )
    def get_constraints_by_group(
        uuid: str,
        group: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Sequence[ConstraintOutput]:
        """
        Get the binding constraint group for the study.

        Args:
        - `uuid`: The UUID of the study.
        - `group`: The name of the binding constraint group (case-insensitive).

        Returns:
        - The list of binding constraints in the group.

        Raises:
        - HTTPException(404) if the group does not exist.
        """
        logger.info(
            f"Fetching binding constraint group '{group}' for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ, params)
        study_interface = study_service.get_study_interface(study)
        result = study_service.binding_constraint_manager.get_constraints_by_group(study_interface, group)
        return result

    @bp.get(
        "/studies/{uuid}/constraint-groups/{group}/validate",
        tags=[APITag.study_data],
        summary="Validate the binding constraint group",
        response_model=None,
    )
    def validate_constraint_group(
        uuid: str,
        group: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> bool:
        """
        Checks if the dimensions of the right-hand side matrices are consistent with
        the dimensions of the binding constraint matrices within the same group.

        Args:
        - `uuid`: The study UUID.
        - `group`: The name of the binding constraint group (case-insensitive).

        Returns:
        - `true` if the group is valid.

        Raises:
        - HTTPException(404) if the group does not exist.
        - HTTPException(422) if the group is invalid.
        """
        logger.info(
            f"Validating binding constraint group '{group}' for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ, params)
        study_interface = study_service.get_study_interface(study)
        return study_service.binding_constraint_manager.validate_constraint_group(study_interface, group)

    @bp.post("/studies/{uuid}/bindingconstraints", tags=[APITag.study_data], summary="Create a binding constraint")
    def create_binding_constraint(
        uuid: str,
        data: ConstraintCreation,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> ConstraintOutput:
        logger.info(
            f"Creating a new binding constraint for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ, params)
        study_interface = study_service.get_study_interface(study)
        return study_service.binding_constraint_manager.create_binding_constraint(study_interface, data)

    @bp.post(
        "/studies/{uuid}/bindingconstraints/{binding_constraint_id}",
        tags=[APITag.study_data],
        summary="Duplicates a given binding constraint",
    )
    def duplicate_binding_constraint(
        uuid: str,
        binding_constraint_id: str,
        new_constraint_name: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> ConstraintOutput:
        logger.info(
            f"Duplicates constraint {binding_constraint_id} for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, params)
        study_interface = study_service.get_study_interface(study)
        return study_service.binding_constraint_manager.duplicate_binding_constraint(
            study_interface, binding_constraint_id, new_constraint_name
        )

    @bp.delete(
        "/studies/{uuid}/bindingconstraints/{binding_constraint_id}",
        tags=[APITag.study_data],
        summary="Delete a binding constraint",
        response_model=None,
    )
    def delete_binding_constraint(
        uuid: str, binding_constraint_id: str, current_user: JWTUser = Depends(auth.get_current_user)
    ) -> None:
        logger.info(
            f"Deleting the binding constraint {binding_constraint_id} for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, params)
        study_interface = study_service.get_study_interface(study)
        return study_service.binding_constraint_manager.remove_binding_constraint(
            study_interface, binding_constraint_id
        )

    @bp.delete(
        "/studies/{uuid}/bindingconstraints",
        tags=[APITag.study_data],
        summary="Delete multiple binding constraints",
        response_model=None,
    )
    def delete_multiple_binding_constraints(
        uuid: str, binding_constraints_ids: List[str], current_user: JWTUser = Depends(auth.get_current_user)
    ) -> None:
        logger.info(
            f"Deleting the binding constraints {binding_constraints_ids!r} for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, params)
        study_interface = study_service.get_study_interface(study)
        return study_service.binding_constraint_manager.remove_multiple_binding_constraints(
            study_interface, binding_constraints_ids
        )

    @bp.post(
        "/studies/{uuid}/bindingconstraints/{binding_constraint_id}/term",
        tags=[APITag.study_data],
        summary="Create a binding constraint term",
    )
    def add_constraint_term(
        uuid: str,
        binding_constraint_id: str,
        term: ConstraintTerm,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> None:
        """
        Append a new term to a given binding constraint

        Args:
        - `uuid`: The UUID of the study.
        - `binding_constraint_id`: The binding constraint ID.
        - `term`: The term to create.
        """
        logger.info(
            f"Add constraint term {term.id} to {binding_constraint_id} for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, params)
        study_interface = study_service.get_study_interface(study)
        return study_service.binding_constraint_manager.create_constraint_terms(
            study_interface, binding_constraint_id, [term]
        )

    @bp.post(
        "/studies/{uuid}/bindingconstraints/{binding_constraint_id}/terms",
        tags=[APITag.study_data],
        summary="Create terms for a given binding constraint",
    )
    def add_constraint_terms(
        uuid: str,
        binding_constraint_id: str,
        terms: Sequence[ConstraintTerm],
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> None:
        """
        Append new terms to a given binding constraint

        Args:
        - `uuid`: The UUID of the study.
        - `binding_constraint_id`: The binding constraint ID.
        - `terms`: The list of terms to create.
        """
        logger.info(
            f"Adding constraint terms to {binding_constraint_id} for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, params)
        study_interface = study_service.get_study_interface(study)
        return study_service.binding_constraint_manager.create_constraint_terms(
            study_interface, binding_constraint_id, terms
        )

    @bp.put(
        "/studies/{uuid}/bindingconstraints/{binding_constraint_id}/term",
        tags=[APITag.study_data],
        summary="Update a binding constraint term",
    )
    def update_constraint_term(
        uuid: str,
        binding_constraint_id: str,
        term: ConstraintTerm,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> None:
        """
        Update a term for a given binding constraint

        Args:
        - `uuid`: The UUID of the study.
        - `binding_constraint_id`: The binding constraint ID.
        - `term`: The term to update.
        """
        logger.info(
            f"Update constraint term {term.id} from {binding_constraint_id} for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, params)
        study_interface = study_service.get_study_interface(study)
        return study_service.binding_constraint_manager.update_constraint_terms(
            study_interface, binding_constraint_id, [term]
        )

    @bp.put(
        "/studies/{uuid}/bindingconstraints/{binding_constraint_id}/terms",
        tags=[APITag.study_data],
        summary="Update terms for a given binding constraint",
    )
    def update_constraint_terms(
        uuid: str,
        binding_constraint_id: str,
        terms: Sequence[ConstraintTerm],
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> None:
        """
        Update several terms for a given binding constraint

        Args:
        - `uuid`: The UUID of the study.
        - `binding_constraint_id`: The binding constraint ID.
        - `terms`: The list of terms to update.
        """
        logger.info(
            f"Updating constraint terms from {binding_constraint_id} for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, params)
        study_interface = study_service.get_study_interface(study)
        return study_service.binding_constraint_manager.update_constraint_terms(
            study_interface, binding_constraint_id, terms
        )

    @bp.delete(
        "/studies/{uuid}/bindingconstraints/{binding_constraint_id}/term/{term_id}",
        tags=[APITag.study_data],
        summary="Remove a binding constraint term",
    )
    def remove_constraint_term(
        uuid: str,
        binding_constraint_id: str,
        term_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> None:
        logger.info(
            f"Remove constraint term {term_id} from {binding_constraint_id} for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, params)
        study_interface = study_service.get_study_interface(study)
        study_service.binding_constraint_manager.remove_constraint_term(study_interface, binding_constraint_id, term_id)

    @bp.get(
        path="/studies/{uuid}/areas/hydro/allocation/matrix",
        tags=[APITag.study_data],
        summary="Get the hydraulic allocation matrix for all areas",
        response_model=AllocationMatrix,
    )
    def get_allocation_matrix(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> AllocationMatrix:
        """
        Get the hydraulic allocation matrix for all areas.

        Args:
        - `uuid`: The study UUID.

        Returns the data frame matrix, where:
        - the rows are the areas,
        - the columns are the hydraulic structures,
        - the values are the allocation factors.
        """
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ, params)
        all_areas = cast(
            List[AreaInfoDTO],  # because `ui=False`
            study_service.get_all_areas(uuid, area_type=AreaType.AREA, ui=False, params=params),
        )
        study_interface = study_service.get_study_interface(study)
        return study_service.allocation_manager.get_allocation_matrix(study_interface, all_areas)

    @bp.get(
        path="/studies/{uuid}/areas/{area_id}/hydro/allocation/form",
        tags=[APITag.study_data],
        summary="Get the form fields used for the allocation form",
        response_model=AllocationFormFields,
    )
    def get_allocation_form_fields(
        uuid: str,
        area_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> AllocationFormFields:
        """
        Get the form fields used for the allocation form.

        Args:
        - `uuid`: The study UUID,
        - `area_id`: the area ID.

        Returns the allocation form fields.
        """
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ, params)
        all_areas = cast(
            List[AreaInfoDTO],  # because `ui=False`
            study_service.get_all_areas(uuid, area_type=AreaType.AREA, ui=False, params=params),
        )
        study_interface = study_service.get_study_interface(study)
        return study_service.allocation_manager.get_allocation_form_fields(all_areas, study_interface, area_id)

    @bp.put(
        path="/studies/{uuid}/areas/{area_id}/hydro/allocation/form",
        tags=[APITag.study_data],
        summary="Update the form fields used for the allocation form",
        status_code=HTTPStatus.OK,
        response_model=AllocationFormFields,
    )
    def set_allocation_form_fields(
        uuid: str,
        area_id: str,
        data: AllocationFormFields = Body(
            ...,
            example=AllocationFormFields(
                allocation=[
                    AllocationField.model_validate({"areaId": "EAST", "coefficient": 1}),
                    AllocationField.model_validate({"areaId": "NORTH", "coefficient": 0.20}),
                ]
            ),
        ),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> AllocationFormFields:
        """
        Update the hydraulic allocation of a given area.

        Args:
        - `uuid`: The study UUID,
        - `area_id`: the area ID.

        Returns the updated allocation form fields.
        """
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, params)
        all_areas = cast(
            List[AreaInfoDTO],  # because `ui=False`
            study_service.get_all_areas(uuid, area_type=AreaType.AREA, ui=False, params=params),
        )
        study_interface = study_service.get_study_interface(study)
        return study_service.allocation_manager.set_allocation_form_fields(all_areas, study_interface, area_id, data)

    @bp.get(
        path="/studies/{uuid}/areas/hydro/correlation/matrix",
        tags=[APITag.study_data],
        summary="Get the hydraulic/load/solar/wind correlation matrix of a study",
        response_model=CorrelationMatrix,
    )
    def get_correlation_matrix(
        uuid: str,
        columns: Optional[str] = Query(
            default=None,
            openapi_examples={
                "all areas": {
                    "description": "get the correlation matrix for all areas (by default)",
                    "value": "",
                },
                "single area": {
                    "description": "get the correlation column for a single area",
                    "value": "north",
                },
                "selected areas": {
                    "description": "get the correlation columns for a selected list of areas",
                    "value": "north,east",
                },
            },
        ),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> CorrelationMatrix:
        """
        Get the hydraulic/load/solar/wind correlation matrix of a study.

        Args:
        - `uuid`: The UUID of the study.
        - `columns`: a filter on the area identifiers:
          - Use no parameter to select all areas.
          - Use an area identifier to select a single area.
          - Use a comma-separated list of areas to select those areas.

        Returns the hydraulic/load/solar/wind correlation matrix with the following attributes:
        - `index`: a list of all study areas.
        - `columns`: a list of selected production areas.
        - `data`: a 2D-array matrix of correlation coefficients with values in the range of -1 to 1.
        """
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ, params)
        all_areas = cast(
            List[AreaInfoDTO],  # because `ui=False`
            study_service.get_all_areas(uuid, area_type=AreaType.AREA, ui=False, params=params),
        )
        study_interface = study_service.get_study_interface(study)
        return study_service.correlation_manager.get_correlation_matrix(
            all_areas,
            study_interface,
            columns.split(",") if columns else [],
        )

    @bp.put(
        path="/studies/{uuid}/areas/hydro/correlation/matrix",
        tags=[APITag.study_data],
        summary="Set the hydraulic/load/solar/wind correlation matrix of a study",
        status_code=HTTPStatus.OK,
        response_model=CorrelationMatrix,
    )
    def set_correlation_matrix(
        uuid: str,
        matrix: CorrelationMatrix = Body(
            ...,
            example={
                "columns": ["north", "east", "south", "west"],
                "data": [
                    [0.0, 0.0, 0.25, 0.0],
                    [0.0, 0.0, 0.75, 0.12],
                    [0.25, 0.75, 0.0, 0.75],
                    [0.0, 0.12, 0.75, 0.0],
                ],
                "index": ["north", "east", "south", "west"],
            },
        ),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> CorrelationMatrix:
        """
        Set the hydraulic/load/solar/wind correlation matrix of a study.

        Args:
        - `uuid`: The UUID of the study.
        - `index`: a list of all study areas.
        - `columns`: a list of selected production areas.
        - `data`: a 2D-array matrix of correlation coefficients with values in the range of -1 to 1.

        Returns the hydraulic/load/solar/wind correlation matrix updated
        """
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, params)
        all_areas = cast(
            List[AreaInfoDTO],  # because `ui=False`
            study_service.get_all_areas(uuid, area_type=AreaType.AREA, ui=False, params=params),
        )
        study_interface = study_service.get_study_interface(study)
        return study_service.correlation_manager.set_correlation_matrix(all_areas, study_interface, matrix)

    @bp.get(
        path="/studies/{uuid}/areas/{area_id}/hydro/correlation/form",
        tags=[APITag.study_data],
        summary="Get the form fields used for the correlation form",
        response_model=CorrelationFormFields,
    )
    def get_correlation_form_fields(
        uuid: str,
        area_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> CorrelationFormFields:
        """
        Get the form fields used for the correlation form.

        Args:
        - `uuid`: The UUID of the study.
        - `area_id`: the area ID.

        Returns the correlation form fields in percentage.
        """
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ, params)
        all_areas = cast(
            List[AreaInfoDTO],  # because `ui=False`
            study_service.get_all_areas(uuid, area_type=AreaType.AREA, ui=False, params=params),
        )
        study_interface = study_service.get_study_interface(study)
        return study_service.correlation_manager.get_correlation_form_fields(all_areas, study_interface, area_id)

    @bp.put(
        path="/studies/{uuid}/areas/{area_id}/hydro/correlation/form",
        tags=[APITag.study_data],
        summary="Set the form fields used for the correlation form",
        status_code=HTTPStatus.OK,
        response_model=CorrelationFormFields,
    )
    def set_correlation_form_fields(
        uuid: str,
        area_id: str,
        data: CorrelationFormFields = Body(
            ...,
            example=CorrelationFormFields(
                correlation=[
                    AreaCoefficientItem.model_validate({"areaId": "east", "coefficient": 80}),
                    AreaCoefficientItem.model_validate({"areaId": "north", "coefficient": 20}),
                ]
            ),
        ),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> CorrelationFormFields:
        """
        Update the hydraulic/load/solar/wind correlation of a given area.

        Args:
        - `uuid`: The UUID of the study.
        - `area_id`: the area ID.

        Returns the correlation form fields in percentage.
        """
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, params)
        all_areas = cast(
            List[AreaInfoDTO],  # because `ui=False`
            study_service.get_all_areas(uuid, area_type=AreaType.AREA, ui=False, params=params),
        )
        study_interface = study_service.get_study_interface(study)
        return study_service.correlation_manager.set_correlation_form_fields(all_areas, study_interface, area_id, data)

    @bp.get(
        path="/studies/{uuid}/config/advancedparameters/form",
        tags=[APITag.study_data],
        summary="Get Advanced parameters form values",
        response_model=AdvancedParamsFormFields,
        response_model_exclude_none=True,
    )
    def get_advanced_parameters(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> AdvancedParamsFormFields:
        logger.info(
            msg=f"Getting Advanced Parameters for study {uuid}",
            extra={"user": current_user.id},
        )

        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ, params)
        study_interface = study_service.get_study_interface(study)
        return study_service.advanced_parameters_manager.get_field_values(study_interface)

    @bp.put(
        path="/studies/{uuid}/config/advancedparameters/form",
        tags=[APITag.study_data],
        summary="Set Advanced parameters new values",
    )
    def set_advanced_parameters(
        uuid: str,
        field_values: AdvancedParamsFormFields,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> None:
        logger.info(
            f"Updating Advanced parameters values for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, params)
        study_interface = study_service.get_study_interface(study)
        study_service.advanced_parameters_manager.set_field_values(study_interface, field_values)

    @bp.put(
        "/studies/{uuid}/timeseries/generate",
        tags=[APITag.study_data],
        summary="Generate timeseries",
    )
    def generate_timeseries(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> str:
        """
        Generates time-series for thermal clusters and put them inside input data.

        Args:
        - `uuid`: The UUID of the study.
        """
        logger.info(
            f"Generating timeseries for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, params)
        return study_service.generate_timeseries(study, params)

    @bp.get(
        path="/studies/{uuid}/areas/{area_id}/properties/form",
        tags=[APITag.study_data],
        summary="Get properties for a given area",
        response_model=PropertiesFormFields,
        response_model_exclude_none=True,
    )
    def get_properties_form_values(
        uuid: str,
        area_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> PropertiesFormFields:
        logger.info(
            "Getting properties form values for study %s and area %s",
            uuid,
            area_id,
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ, params)
        study_interface = study_service.get_study_interface(study)
        return study_service.properties_manager.get_field_values(study_interface, area_id)

    @bp.put(
        path="/studies/{uuid}/areas/{area_id}/properties/form",
        tags=[APITag.study_data],
        summary="Set properties for a given area",
    )
    def set_properties_form_values(
        uuid: str,
        area_id: str,
        form_fields: PropertiesFormFields,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> None:
        logger.info(
            "Setting properties form values for study %s and area %s",
            uuid,
            area_id,
            extra={"user": current_user.id},
        )
        request_params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, request_params)
        study_interface = study_service.get_study_interface(study)
        study_service.properties_manager.set_field_values(study_interface, area_id, form_fields)

    @bp.get(
        path="/studies/{uuid}/areas/{area_id}/clusters/renewable",
        tags=[APITag.study_data],
        summary="Get all renewable clusters",
        response_model=Sequence[RenewableClusterOutput],
    )
    def get_renewable_clusters(
        uuid: str,
        area_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Sequence[RenewableClusterOutput]:
        logger.info(
            "Getting renewable clusters for study %s and area %s",
            uuid,
            area_id,
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ, params)
        study_interface = study_service.get_study_interface(study)
        return study_service.renewable_manager.get_clusters(study_interface, area_id)

    @bp.get(
        path="/studies/{uuid}/areas/{area_id}/clusters/renewable/{cluster_id}",
        tags=[APITag.study_data],
        summary="Get a single renewable cluster",
        response_model=RenewableClusterOutput,
    )
    def get_renewable_cluster(
        uuid: str,
        area_id: str,
        cluster_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> RenewableClusterOutput:
        logger.info(
            "Getting renewable cluster values for study %s and cluster %s",
            uuid,
            cluster_id,
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ, params)
        study_interface = study_service.get_study_interface(study)
        return study_service.renewable_manager.get_cluster(study_interface, area_id, cluster_id)

    @bp.get(
        path="/studies/{uuid}/areas/{area_id}/clusters/renewable/{cluster_id}/form",
        tags=[APITag.study_data],
        summary="Get renewable configuration for a given cluster (deprecated)",
        response_class=RedirectResponse,
        deprecated=True,
    )
    def redirect_get_renewable_cluster(
        uuid: str,
        area_id: str,
        cluster_id: str,
    ) -> str:
        return f"/v1/studies/{uuid}/areas/{area_id}/clusters/renewable/{cluster_id}"

    @bp.post(
        path="/studies/{uuid}/areas/{area_id}/clusters/renewable",
        tags=[APITag.study_data],
        summary="Create a new renewable cluster",
        response_model=RenewableClusterOutput,
    )
    def create_renewable_cluster(
        uuid: str,
        area_id: str,
        cluster_data: RenewableClusterCreation,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> RenewableClusterOutput:
        """
        Create a new renewable cluster.

        Args:
        - `uuid`: The UUID of the study.
        - `area_id`: the area ID.
        - `cluster_data`: the properties used for creation:
          "name" and "group".

        Returns: The properties of the newly-created renewable cluster.
        """
        logger.info(
            f"Creating renewable cluster for study '{uuid}' and area '{area_id}'",
            extra={"user": current_user.id},
        )
        request_params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, request_params)
        study_interface = study_service.get_study_interface(study)
        return study_service.renewable_manager.create_cluster(study_interface, area_id, cluster_data)

    @bp.patch(
        path="/studies/{uuid}/areas/{area_id}/clusters/renewable/{cluster_id}",
        tags=[APITag.study_data],
        summary="Update a renewable cluster",
        response_model=RenewableClusterOutput,
    )
    def update_renewable_cluster(
        uuid: str,
        area_id: str,
        cluster_id: str,
        cluster_data: RenewableClusterUpdate,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> RenewableClusterOutput:
        logger.info(
            f"Updating renewable cluster for study '{uuid}' and cluster '{cluster_id}'",
            extra={"user": current_user.id},
        )
        request_params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, request_params)
        study_interface = study_service.get_study_interface(study)
        return study_service.renewable_manager.update_cluster(study_interface, area_id, cluster_id, cluster_data)

    @bp.put(
        path="/studies/{uuid}/areas/{area_id}/clusters/renewable/{cluster_id}/form",
        tags=[APITag.study_data],
        summary="Get renewable configuration for a given cluster (deprecated)",
        response_model=RenewableClusterOutput,
        deprecated=True,
    )
    def redirect_update_renewable_cluster(
        uuid: str,
        area_id: str,
        cluster_id: str,
        cluster_data: RenewableClusterUpdate,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> RenewableClusterOutput:
        # We cannot perform redirection, because we have a PUT, where a PATCH is required.
        return update_renewable_cluster(uuid, area_id, cluster_id, cluster_data, current_user=current_user)

    @bp.delete(
        path="/studies/{uuid}/areas/{area_id}/clusters/renewable",
        tags=[APITag.study_data],
        summary="Remove renewable clusters",
        status_code=HTTPStatus.NO_CONTENT,
        response_model=None,
    )
    def delete_renewable_clusters(
        uuid: str,
        area_id: str,
        cluster_ids: Sequence[str],
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> None:
        """
        Remove one or several renewable cluster(s) and it's time series.

        Args:
        - `uuid`: The UUID of the study.
        - `area_id`: the area ID.
        - `cluster_ids`: list of IDs to remove.
        """
        logger.info(
            f"Deleting renewable clusters {cluster_ids!r} for study '{uuid}' and area '{area_id}'",
            extra={"user": current_user.id},
        )
        request_params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, request_params)
        study_interface = study_service.get_study_interface(study)
        study_service.renewable_manager.delete_clusters(study_interface, area_id, cluster_ids)

    @bp.get(
        path="/studies/{uuid}/areas/{area_id}/clusters/thermal",
        tags=[APITag.study_data],
        summary="Get thermal clusters for a given area",
        response_model=Sequence[ThermalClusterOutput],
    )
    def get_thermal_clusters(
        uuid: str,
        area_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Sequence[ThermalClusterOutput]:
        """
        Retrieve the list of thermal clusters for a specified area.

        Args:
        - `uuid`: The UUID of the study.
        - `area_id`: the area ID.

        Returns: The list thermal clusters.
        """
        logger.info(
            "Getting thermal clusters for study %s and area %s",
            uuid,
            area_id,
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ, params)
        study_interface = study_service.get_study_interface(study)
        return study_service.thermal_manager.get_clusters(study_interface, area_id)

    @bp.get(
        path="/studies/{uuid}/areas/{area_id}/clusters/thermal/{cluster_id}",
        tags=[APITag.study_data],
        summary="Get thermal configuration for a given cluster",
        response_model=ThermalClusterOutput,
    )
    def get_thermal_cluster(
        uuid: str,
        area_id: str,
        cluster_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> ThermalClusterOutput:
        """
        Retrieve the thermal clusters for a specified area.

        Args:
        - `uuid`: The UUID of the study.
        - `area_id`: the area ID.
        - `cluster_id`: the cluster ID.

        Returns: The properties of the thermal clusters.
        """
        logger.info(
            "Getting thermal cluster values for study %s and cluster %s",
            uuid,
            cluster_id,
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ, params)
        study_interface = study_service.get_study_interface(study)
        return study_service.thermal_manager.get_cluster(study_interface, area_id, cluster_id)

    @bp.get(
        path="/studies/{uuid}/areas/{area_id}/clusters/thermal/{cluster_id}/form",
        tags=[APITag.study_data],
        summary="Get thermal configuration for a given cluster (deprecated)",
        response_class=RedirectResponse,
        deprecated=True,
    )
    def redirect_get_thermal_cluster(
        uuid: str,
        area_id: str,
        cluster_id: str,
    ) -> str:
        return f"/v1/studies/{uuid}/areas/{area_id}/clusters/thermal/{cluster_id}"

    @bp.post(
        path="/studies/{uuid}/areas/{area_id}/clusters/thermal",
        tags=[APITag.study_data],
        summary="Create a new thermal cluster for a given area",
        response_model=ThermalClusterOutput,
    )
    def create_thermal_cluster(
        uuid: str,
        area_id: str,
        cluster_data: ThermalClusterCreation,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> ThermalClusterOutput:
        """
        Create a new thermal cluster for a specified area.

        Args:
        - `uuid`: The UUID of the study.
        - `area_id`: the area ID.
        - `cluster_data`: the properties used for creation:
          "name" and "group".

        Returns: The properties of the newly-created thermal cluster.
        """
        logger.info(
            f"Creating thermal cluster for study '{uuid}' and area '{area_id}'",
            extra={"user": current_user.id},
        )
        request_params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, request_params)
        study_interface = study_service.get_study_interface(study)
        return study_service.thermal_manager.create_cluster(study_interface, area_id, cluster_data)

    @bp.patch(
        path="/studies/{uuid}/areas/{area_id}/clusters/thermal/{cluster_id}",
        tags=[APITag.study_data],
        summary="Update thermal cluster for a given area",
        response_model=ThermalClusterOutput,
    )
    def update_thermal_cluster(
        uuid: str,
        area_id: str,
        cluster_id: str,
        cluster_data: ThermalClusterInput,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> ThermalClusterOutput:
        """
        Update the properties of a thermal cluster for a specified area.

        Args:
        - `uuid`: The UUID of the study.
        - `area_id`: the area ID.
        - `cluster_data`: the properties used for updating.

        Returns: The properties of the updated thermal clusters.
        """
        logger.info(
            f"Updating thermal cluster for study '{uuid}' and cluster '{cluster_id}'",
            extra={"user": current_user.id},
        )
        request_params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, request_params)
        study_interface = study_service.get_study_interface(study)
        return study_service.thermal_manager.update_cluster(study_interface, area_id, cluster_id, cluster_data)

    @bp.put(
        path="/studies/{uuid}/areas/{area_id}/clusters/thermal/{cluster_id}/form",
        tags=[APITag.study_data],
        summary="Get thermal configuration for a given cluster (deprecated)",
        response_model=ThermalClusterOutput,
        deprecated=True,
    )
    def redirect_update_thermal_cluster(
        uuid: str,
        area_id: str,
        cluster_id: str,
        cluster_data: ThermalClusterInput,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> ThermalClusterOutput:
        # We cannot perform redirection, because we have a PUT, where a PATCH is required.
        return update_thermal_cluster(uuid, area_id, cluster_id, cluster_data, current_user=current_user)

    @bp.get(
        path="/studies/{uuid}/areas/{area_id}/clusters/thermal/{cluster_id}/validate",
        tags=[APITag.study_data],
        summary="Validates the thermal cluster series",
    )
    def validate_cluster_series(
        uuid: str,
        area_id: str,
        cluster_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> bool:
        """
        Validate the consistency of all time series for the given thermal cluster.

        Args:
        - `uuid`: The UUID of the study.
        - `area_id`: the area ID.
        - `cluster_id`: the ID of the thermal cluster.

        Permissions:
        - User must have READ permission on the study.
        """
        logger.info(
            f"Validating thermal series values for study {uuid} and cluster {cluster_id}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ, params)
        study_interface = study_service.get_study_interface(study)
        return study_service.thermal_manager.validate_series(study_interface, area_id, cluster_id)

    @bp.delete(
        path="/studies/{uuid}/areas/{area_id}/clusters/thermal",
        tags=[APITag.study_data],
        summary="Remove thermal clusters for a given area",
        status_code=HTTPStatus.NO_CONTENT,
        response_model=None,
    )
    def delete_thermal_clusters(
        uuid: str,
        area_id: str,
        cluster_ids: Sequence[str],
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> None:
        """
        Remove one or several thermal cluster(s) from a specified area.
        This endpoint removes the properties and time series of each thermal clusters.

        Args:
        - `uuid`: The UUID of the study.
        - `area_id`: the area ID.
        - `cluster_ids`: list of thermal cluster IDs to remove.
        """
        logger.info(
            f"Deleting thermal clusters {cluster_ids!r} for study '{uuid}' and area '{area_id}'",
            extra={"user": current_user.id},
        )
        request_params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, request_params)
        study_interface = study_service.get_study_interface(study)
        study_service.asserts_no_thermal_in_binding_constraints(study, area_id, cluster_ids)
        study_service.thermal_manager.delete_clusters(study_interface, area_id, cluster_ids)

    @bp.get(
        path="/studies/{uuid}/areas/{area_id}/storages/{storage_id}",
        tags=[APITag.study_data],
        summary="Get the short-term storage properties",
        response_model=STStorageOutput,
    )
    def get_st_storage(
        uuid: str,
        area_id: str,
        storage_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> STStorageOutput:
        """
        Retrieve the storages by given uuid and area id of a study.

        Args:
        - `uuid`: The UUID of the study.
        - `area_id`: the area ID.
        - `storage_id`: the storage ID of the study.

        Returns: One storage with the following attributes:
        - `id`: the storage ID of the study.
        - `name`: the name of the  storage.
        - `group`: the group of the  storage.
        - `injectionNominalCapacity`: the injection Nominal Capacity of the  storage.
        - `withdrawalNominalCapacity`: the withdrawal Nominal Capacity of the  storage.
        - `reservoirCapacity`: the reservoir capacity of the  storage.
        - `efficiency`: the efficiency of the  storage.
        - `initialLevel`: the initial Level of the  storage.
        - `initialLevelOptim`: the initial Level Optim of the  storage.

        Permissions:
          The user must have READ permission on the study.
        """
        logger.info(
            f"Getting values for study {uuid} and short term storage {storage_id}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ, params)
        study_interface = study_service.get_study_interface(study)
        return study_service.st_storage_manager.get_storage(study_interface, area_id, storage_id)

    @bp.get(
        path="/studies/{uuid}/areas/{area_id}/storages",
        tags=[APITag.study_data],
        summary="Get the list of short-term storage properties",
        response_model=Sequence[STStorageOutput],
    )
    def get_st_storages(
        uuid: str,
        area_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Sequence[STStorageOutput]:
        """
        Retrieve the short-term storages by given uuid and area ID of a study.

        Args:
        - `uuid`: The UUID of the study.
        - `area_id`: the area ID.

        Returns: A list of storages with the following attributes:
        - `id`: the storage ID of the study.
        - `name`: the name of the  storage.
        - `group`: the group of the  storage.
        - `injectionNominalCapacity`: the injection Nominal Capacity of the  storage.
        - `withdrawalNominalCapacity`: the withdrawal Nominal Capacity of the  storage.
        - `reservoirCapacity`: the reservoir capacity of the  storage.
        - `efficiency`: the efficiency of the  storage.
        - `initialLevel`: the initial Level of the  storage.
        - `initialLevelOptim`: the initial Level Optim of the  storage.

        Permissions:
          The user must have READ permission on the study.
        """
        logger.info(
            f"Getting storages for study {uuid} in a given area {area_id}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ, params)
        study_interface = study_service.get_study_interface(study)
        return study_service.st_storage_manager.get_storages(study_interface, area_id)

    @bp.get(
        path="/studies/{uuid}/areas/{area_id}/storages/{storage_id}/series/{ts_name}",
        tags=[APITag.study_data],
        summary="Get a short-term storage time series",
        response_model=STStorageMatrix,
    )
    def get_st_storage_matrix(
        uuid: str,
        area_id: str,
        storage_id: str,
        ts_name: STStorageTimeSeries,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> STStorageMatrix:
        """
        Retrieve the matrix of the specified time series for the given short-term storage.

        Args:
        - `uuid`: The UUID of the study.
        - `area_id`: the area ID.
        - `storage_id`: the ID of the short-term storage.
        - `ts_name`: the name of the time series to retrieve.

        Returns: The time series matrix with the following attributes:
        - `index`: a list of 0-indexed time series lines (8760 lines).
        - `columns`: a list of 0-indexed time series columns (1 column).
        - `data`: a 2D-array matrix representing the time series.

        Permissions:
        - User must have READ permission on the study.
        """
        logger.info(
            f"Retrieving time series for study {uuid} and short-term storage {storage_id}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ, params)
        study_interface = study_service.get_study_interface(study)
        return study_service.st_storage_manager.get_matrix(study_interface, area_id, storage_id, ts_name)

    @bp.put(
        path="/studies/{uuid}/areas/{area_id}/storages/{storage_id}/series/{ts_name}",
        tags=[APITag.study_data],
        summary="Update a short-term storage time series",
    )
    def update_st_storage_matrix(
        uuid: str,
        area_id: str,
        storage_id: str,
        ts_name: STStorageTimeSeries,
        ts: STStorageMatrix,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> None:
        """
        Update the matrix of the specified time series for the given short-term storage.

        Args:
        - `uuid`: The UUID of the study.
        - `area_id`: the area ID.
        - `storage_id`: the ID of the short-term storage.
        - `ts_name`: the name of the time series to retrieve.
        - `ts`: the time series matrix to update.

        Permissions:
        - User must have WRITE permission on the study.
        """
        logger.info(
            f"Update time series for study {uuid} and short-term storage {storage_id}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, params)
        study_interface = study_service.get_study_interface(study)
        study_service.st_storage_manager.update_matrix(study_interface, area_id, storage_id, ts_name, ts)

    @bp.get(
        path="/studies/{uuid}/areas/{area_id}/storages/{storage_id}/validate",
        tags=[APITag.study_data],
        summary="Validate all the short-term storage time series",
    )
    def validate_st_storage_matrices(
        uuid: str,
        area_id: str,
        storage_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> bool:
        """
        Validate the consistency of all time series for the given short-term storage.

        Args:
        - `uuid`: The UUID of the study.
        - `area_id`: the area ID.
        - `storage_id`: the ID of the short-term storage.

        Permissions:
        - User must have READ permission on the study.
        """
        logger.info(
            f"Validating time series for study {uuid} and short-term storage {storage_id}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ, params)
        study_interface = study_service.get_study_interface(study)
        return study_service.st_storage_manager.validate_matrices(study_interface, area_id, storage_id)

    @bp.post(
        path="/studies/{uuid}/areas/{area_id}/storages",
        tags=[APITag.study_data],
        summary="Create a new short-term storage in an area",
        response_model=STStorageOutput,
    )
    def create_st_storage(
        uuid: str,
        area_id: str,
        form: STStorageCreation,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> STStorageOutput:
        """
        Create a new short-term storage in an area.

        Args:
        - `uuid`: The UUID of the study.
        - `area_id`: The area ID.
        - `form`: The characteristic of the storage that we can update:
          - `name`: The name of the updated storage.
          - `group`: The group of the updated storage.
          - `injectionNominalCapacity`: The injection Nominal Capacity of the updated storage.
          - `withdrawalNominalCapacity`: The withdrawal Nominal Capacity of the updated storage.
          - `reservoirCapacity`:  The reservoir capacity of the updated storage.
          - `efficiency`: The efficiency of the updated storage
          - `initialLevel`: The initial Level of the updated storage
          - `initialLevelOptim`: The initial Level Optim of the updated storage

        Returns: New storage with the following attributes:
        - `id`: the storage ID of the study.
        - `name`: the name of the  storage.
        - `group`: the group of the  storage.
        - `injectionNominalCapacity`: the injection Nominal Capacity of the  storage.
        - `withdrawalNominalCapacity`: the withdrawal Nominal Capacity of the  storage.
        - `reservoirCapacity`: the reservoir capacity of the  storage.
        - `efficiency`: the efficiency of the  storage.
        - `initialLevel`: the initial Level of the  storage.
        - `initialLevelOptim`: the initial Level Optim of the  storage.

        Permissions:
        - User must have READ/WRITE permission on the study.
        """

        logger.info(
            f"Create short-term storage from {area_id} for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, params)
        study_interface = study_service.get_study_interface(study)
        return study_service.st_storage_manager.create_storage(study_interface, area_id, form)

    @bp.patch(
        path="/studies/{uuid}/areas/{area_id}/storages/{storage_id}",
        tags=[APITag.study_data],
        summary="Update the short-term storage properties",
    )
    def update_st_storage(
        uuid: str,
        area_id: str,
        storage_id: str,
        form: STStorageUpdate,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> STStorageOutput:
        """
        Update short-term storage of a study.

        Args:
        - `uuid`: The UUID of the study.
        - `area_id`: the area ID.
        - `storage_id`: the storage id of the study that we want to update.
        - `form`: the characteristic of the storage that we can update:
          - `name`: the name of the updated storage.
          - `group`: the group of the updated storage.
          - `injectionNominalCapacity`: the injection Nominal Capacity of the updated storage.
          - `withdrawalNominalCapacity`: the withdrawal Nominal Capacity of the updated storage.
          - `reservoirCapacity`:  The reservoir capacity of the updated storage.
          - `efficiency`: the efficiency of the updated storage
          - `initialLevel`: the initial Level of the updated storage
          - `initialLevelOptim`: the initial Level Optim of the updated storage

        Returns: The updated storage with the following attributes:
        - `name`: the name of the updated storage.
        - `group`: the group of the updated storage.
        - `injectionNominalCapacity`: the injection Nominal Capacity of the updated storage.
        - `withdrawalNominalCapacity`: the withdrawal Nominal Capacity of the updated storage.
        - `reservoirCapacity`:  The reservoir capacity of the updated storage.
        - `efficiency`: the efficiency of the updated storage
        - `initialLevel`: the initial Level of the updated storage
        - `initialLevelOptim`: the initial Level Optim of the updated storage
        - `id`: the storage ID of the study that we want to update.

        Permissions:
        - User must have READ/WRITE permission on the study.
        """

        logger.info(
            f"Update short-term storage {storage_id} from {area_id} for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, params)
        study_interface = study_service.get_study_interface(study)
        return study_service.st_storage_manager.update_storage(study_interface, area_id, storage_id, form)

    @bp.delete(
        path="/studies/{uuid}/areas/{area_id}/storages",
        tags=[APITag.study_data],
        summary="Remove short-term storages from an area",
        status_code=HTTPStatus.NO_CONTENT,
    )
    def delete_st_storages(
        uuid: str,
        area_id: str,
        storage_ids: Sequence[str],
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> None:
        """
        Delete short-term storages from an area.

        Args:
        - `uuid`: The UUID of the study.
        - `area_id`: the area ID.
        - `storage_ids`: ist of IDs of the storages to remove from the area.

        Permissions:
        - User must have DELETED permission on the study.
        """
        logger.info(
            f"Delete short-term storage ID's {storage_ids} from {area_id} for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, params)
        study_interface = study_service.get_study_interface(study)
        study_service.st_storage_manager.delete_storages(study_interface, area_id, storage_ids)

    @bp.post(
        path="/studies/{uuid}/areas/{area_id}/{cluster_type}/{source_cluster_id}",
        tags=[APITag.study_data],
        summary="Duplicates a given cluster",
    )
    def duplicate_cluster(
        uuid: str,
        area_id: str,
        cluster_type: ClusterType,
        source_cluster_id: str,
        new_cluster_name: str = Query(..., alias="newName", title="New Cluster Name"),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> STStorageOutput | ThermalClusterOutput | RenewableClusterOutput:
        logger.info(
            f"Duplicates {cluster_type.value} {source_cluster_id} of {area_id} for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE, params)

        manager: STStorageManager | RenewableManager | ThermalManager
        if cluster_type == ClusterType.ST_STORAGES:
            manager = study_service.st_storage_manager
        elif cluster_type == ClusterType.RENEWABLES:
            manager = study_service.renewable_manager
        elif cluster_type == ClusterType.THERMALS:
            manager = study_service.thermal_manager
        else:  # pragma: no cover
            raise NotImplementedError(f"Cluster type {cluster_type} not implemented")

        study_interface = study_service.get_study_interface(study)
        return manager.duplicate_cluster(study_interface, area_id, source_cluster_id, new_cluster_name)

    return bp
