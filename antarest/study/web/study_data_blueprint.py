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

import enum
import logging
from http import HTTPStatus
from typing import Dict, List, Literal, Mapping, Optional, Sequence

import typing_extensions as te
from fastapi import APIRouter, Body, Query
from pydantic import ConfigDict, Field, RootModel
from starlette.responses import RedirectResponse

from antarest.core.config import Config
from antarest.core.model import JSON, StudyPermissionType
from antarest.core.utils.utils import sanitize_uuid
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth
from antarest.matrixstore.matrix_editor import MatrixEditInstruction
from antarest.study.business.areas.renewable_management import RenewableManager
from antarest.study.business.areas.st_storage_management import STStorageManager
from antarest.study.business.areas.thermal_management import (
    ThermalManager,
)
from antarest.study.business.binding_constraint_management import ConstraintFilters
from antarest.study.business.model.area_model import AreaCreation, AreaInfo, AreaType, AreaUIData, AreaUIUpdate
from antarest.study.business.model.area_properties_model import AreaProperties, AreaPropertiesUpdate
from antarest.study.business.model.binding_constraint_model import (
    BindingConstraint,
    BindingConstraintCreationWithMatrices,
    BindingConstraintFrequency,
    BindingConstraintOperator,
    BindingConstraintUpdateWithMatrices,
    ConstraintTerm,
    ConstraintTermUpdate,
)
from antarest.study.business.model.config.adequacy_patch_model import (
    AdequacyPatchParameters,
    AdequacyPatchParametersUpdate,
)
from antarest.study.business.model.config.advanced_parameters_model import AdvancedParameters, AdvancedParametersUpdate
from antarest.study.business.model.config.compatibility_parameters_model import (
    CompatibilityParameters,
    CompatibilityParametersUpdate,
)
from antarest.study.business.model.config.general_model import GeneralConfig, GeneralConfigUpdate
from antarest.study.business.model.config.optimization_config_model import (
    OptimizationPreferences,
    OptimizationPreferencesUpdate,
)
from antarest.study.business.model.config.playlist_model import PlaylistUpdate, PlaylistValues, PlaylistValuesUpdate
from antarest.study.business.model.config.timeseries_config_model import (
    TimeSeriesConfiguration,
    TimeSeriesConfigurationUpdate,
)
from antarest.study.business.model.district_model import (
    DistrictCreation,
    DistrictDTO,
    DistrictUpdate,
)
from antarest.study.business.model.hydro_allocation_model import (
    HydroAllocation,
    HydroAllocationArea,
    HydroAllocationMatrix,
)
from antarest.study.business.model.hydro_correlation_model import (
    HydroCorrelation,
    HydroCorrelationArea,
    HydroCorrelationMatrix,
)
from antarest.study.business.model.hydro_model import (
    HydroManagement,
    HydroManagementUpdate,
    InflowStructure,
    InflowStructureUpdate,
)
from antarest.study.business.model.layer_model import Layer
from antarest.study.business.model.link_model import Link, LinkUpdate
from antarest.study.business.model.renewable_cluster_model import (
    RenewableCluster,
    RenewableClusterCreation,
    RenewableClusterUpdate,
)
from antarest.study.business.model.scenario_builder_model import AnyScenarios, ScenarioType
from antarest.study.business.model.sts_model import (
    STStorage,
    STStorageAdditionalConstraint,
    STStorageAdditionalConstraintCreation,
    STStorageAdditionalConstraintUpdate,
    STStorageCreation,
    STStorageUpdate,
)
from antarest.study.business.model.study_data_model import StudyDataDTO
from antarest.study.business.model.thematic_trimming_model import ThematicTrimming, ThematicTrimmingUpdate
from antarest.study.business.model.thermal_cluster_model import (
    ThermalCluster,
    ThermalClusterCreation,
    ThermalClusterUpdate,
)
from antarest.study.business.table_mode_management import TableDataDTO, TableModeType
from antarest.study.model import CommentsDto
from antarest.study.service import StudyService
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.web.views.scenario_builder_views import RulesetsView, rulesets_model_to_view, rulesets_view_to_model

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


class PlaylistRootModel(RootModel[dict[int, PlaylistValues]]):
    model_config = ConfigDict(json_schema_extra={"example": {"1": {"status": False, "weight": 0.4}}})


class PlaylistUpdateRootModel(RootModel[dict[int, PlaylistValuesUpdate]]):
    model_config = ConfigDict(json_schema_extra={"example": {"1": {"status": False, "weight": 0.4}}})


def create_study_data_routes(study_service: StudyService, config: Config) -> APIRouter:
    """
    Endpoint implementation for studies area management

    Args:
        study_service: study service facade to handle request
        config: main server configuration

    Returns:
        The FastAPI route for Study data management
    """
    auth = Auth(config)
    bp = APIRouter(prefix="/v1", dependencies=[auth.required()], tags=[APITag.study_data])

    class AreaResponse(AreaInfo):
        """API view for areas with deprecated ``type`` field kept for compatibility."""

        type: Literal[AreaType.AREA] = Field(
            default=AreaType.AREA,
            json_schema_extra={"deprecated": True},
        )

    @bp.get(
        "/studies/{uuid}/comments",
        summary="Get comments",
    )
    def get_comments(uuid: str) -> str:
        logger.info(f"Get comments of study {uuid}")
        study_id = sanitize_uuid(uuid)
        return study_service.get_comments(study_id)

    @bp.put(
        "/studies/{uuid}/comments",
        status_code=HTTPStatus.NO_CONTENT,
        summary="Update comments",
    )
    def edit_comments(uuid: str, data: CommentsDto) -> None:
        logger.info(f"Editing comments for study {uuid}")
        study_id = sanitize_uuid(uuid)
        study_service.set_comments(study_id, data.comments)

    @bp.get(
        "/studies/{uuid}/areas",
        summary="Get all areas basic info",
    )
    def get_areas(
        uuid: str,
        type: Optional[AreaType] = Query(default=None, deprecated=True),
        ui: bool = Query(default=False),
    ) -> List[AreaResponse] | Dict[str, AreaUIData]:
        logger.info(f"Fetching area list (type={type}, ui={ui}) for study {uuid}")
        if ui:
            return study_service.get_all_areas_ui_info(uuid)

        areas = study_service.get_all_areas_info(uuid)
        return [AreaResponse.model_validate(area.model_dump()) for area in areas]

    @bp.get("/studies/{uuid}/links", summary="Get all links")
    def get_links(uuid: str) -> List[Link]:
        logger.info(f"Fetching link list for study {uuid}")
        areas_list = study_service.get_all_links(uuid)
        return areas_list

    @bp.post(
        "/studies/{uuid}/areas",
        summary="Create a new area",
    )
    def create_area(uuid: str, area_creation_info: AreaCreation) -> AreaResponse:
        logger.info(f"Creating new area for study {uuid}")
        area = study_service.create_area(uuid, area_creation_info)
        return AreaResponse.model_validate(area.model_dump())

    @bp.post("/studies/{uuid}/links", summary="Create a link")
    def create_link(
        uuid: str,
        link_creation_info: Link,
    ) -> Link:
        logger.info(f"Creating new link for study {uuid}")
        return study_service.create_link(uuid, link_creation_info)

    @bp.put("/studies/{uuid}/links/{area_from}/{area_to}", summary="Update a link")
    def update_link(uuid: str, area_from: str, area_to: str, link_update_dto: LinkUpdate) -> Link:
        logger.info(f"Updating link {area_from} -> {area_to} for study {uuid}")
        return study_service.update_link(uuid, area_from, area_to, link_update_dto)

    @bp.put(
        "/studies/{uuid}/areas/{area_id}/ui",
        summary="Update area information",
    )
    def update_area_ui(uuid: str, area_id: str, area_ui: AreaUIUpdate, layer: str = "0") -> None:
        logger.info(f"Updating area ui {area_id} for study {uuid}")
        study_service.update_area_ui(uuid, area_id, area_ui, layer)

    @bp.delete(
        "/studies/{uuid}/areas/{area_id}",
        summary="Delete an area",
    )
    def delete_area(uuid: str, area_id: str) -> str:
        logger.info(f"Removing area {area_id} in study {uuid}")
        uuid = sanitize_uuid(uuid)
        area_id = transform_name_to_id(area_id)
        study_service.delete_area(uuid, area_id)
        return area_id

    @bp.delete(
        "/studies/{uuid}/links/{area_from}/{area_to}",
        summary="Delete a link",
    )
    def delete_link(uuid: str, area_from: str, area_to: str) -> str:
        logger.info(f"Removing link {area_from}%{area_to} in study {uuid}")
        area_from = transform_name_to_id(area_from)
        area_to = transform_name_to_id(area_to)
        study_service.delete_link(uuid, area_from, area_to)
        return f"{area_from}%{area_to}"

    @bp.get(
        "/studies/{uuid}/layers",
        summary="Get all layers info",
    )
    def get_layers(uuid: str) -> List[Layer]:
        logger.info(f"Fetching layer list for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
        return study_service.layer_manager.get_layers(study_service.get_study_interface(study))

    @bp.post(
        "/studies/{uuid}/layers",
        summary="Create new layer",
    )
    def create_layer(uuid: str, name: str) -> str:
        logger.info(f"Create layer {name} for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        return study_service.layer_manager.create_layer(study_service.get_study_interface(study), name)

    @bp.put(
        "/studies/{uuid}/layers/{layer_id}",
        summary="Update layer",
    )
    def update_layer(uuid: str, layer_id: str, name: str = "", areas: Optional[List[str]] = None) -> None:
        logger.info(f"Updating layer {layer_id} for study {uuid} with name {name}")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        if name:
            study_service.layer_manager.update_layer_name(study_interface, layer_id, name)
        if areas:
            study_service.area_manager.update_layer_areas(study_interface, layer_id, areas)

    @bp.delete(
        "/studies/{uuid}/layers/{layer_id}",
        summary="Remove layer",
        status_code=HTTPStatus.NO_CONTENT,
    )
    def remove_layer(uuid: str, layer_id: str) -> None:
        logger.info(f"Remove layer {layer_id} for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
        study_service.layer_manager.remove_layer(study_service.get_study_interface(study), layer_id)

    @bp.get(
        "/studies/{uuid}/districts",
        summary="Get the list of districts defined in this study",
    )
    def get_districts(uuid: str) -> List[DistrictDTO]:
        logger.info(f"Fetching districts list for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
        study_interface = study_service.get_study_interface(study)
        return list(study_service.district_manager.get_districts(study_interface))

    @bp.post(
        "/studies/{uuid}/districts",
        summary="Create a new district in the study",
    )
    def create_district(uuid: str, district_creation: DistrictCreation) -> DistrictDTO:
        logger.info(f"Create district {district_creation.name} for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        return study_service.district_manager.create_district(study_interface, district_creation)

    @bp.put(
        "/studies/{uuid}/districts/{district_id}",
        summary="Update the properties of a district",
    )
    def update_district(uuid: str, district_id: str, dto: DistrictUpdate) -> None:
        logger.info(f"Updating district {district_id} for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        study_service.district_manager.update_district(study_interface, district_id, dto)

    @bp.delete(
        "/studies/{uuid}/districts/{district_id}",
        summary="Remove a district from a study",
    )
    def remove_district(uuid: str, district_id: str) -> None:
        logger.info(f"Remove district {district_id} for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        study_service.district_manager.remove_district(study_interface, district_id)

    @bp.get(
        "/studies/{uuid}/areas/{area_id}/hydro/form",
        summary="Get Hydro config values for form",
        response_model_exclude_none=True,
    )
    def get_hydro_form_values(uuid: str, area_id: str) -> HydroManagement:
        logger.info(msg=f"Getting Hydro management config for area {area_id} of study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
        study_interface = study_service.get_study_interface(study)
        return study_service.hydro_manager.get_hydro_management(study_interface, area_id)

    @bp.put(
        "/studies/{uuid}/areas/{area_id}/hydro/form",
        summary="Set Hydro config with values from form",
    )
    def set_hydro_form_values(uuid: str, area_id: str, data: HydroManagementUpdate) -> None:
        logger.info(msg=f"Updating Hydro management config for area {area_id} of study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        study_service.hydro_manager.update_hydro_management(study_interface, data, area_id)

    # noinspection SpellCheckingInspection
    @bp.get(
        "/studies/{uuid}/areas/{area_id}/hydro/inflow-structure",
        summary="Get inflow properties",
    )
    def get_inflow_structure(uuid: str, area_id: str) -> InflowStructure:
        """Get the configuration for the hydraulic inflow structure of the given area."""
        logger.info(msg=f"Getting inflow structure values for area {area_id} of study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
        study_interface = study_service.get_study_interface(study)
        return study_service.hydro_manager.get_inflow_structure(study_interface, area_id)

    @bp.put(
        "/studies/{uuid}/areas/{area_id}/hydro/inflow-structure",
        summary="Update inflow properties values",
    )
    def update_inflow_structure(uuid: str, area_id: str, values: InflowStructureUpdate) -> None:
        """Update the configuration for the hydraulic inflow properties of the given area."""
        logger.info(msg=f"Updating inflow properties values for area {area_id} of study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        study_service.hydro_manager.update_inflow_structure(study_interface, area_id, values)

    @bp.put(
        "/studies/{uuid}/matrix",
        summary="Edit matrix",
    )
    def edit_matrix(uuid: str, path: str, matrix_edit_instructions: List[MatrixEditInstruction] = Body(...)) -> None:
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
        study_service.update_matrix(uuid, path, matrix_edit_instructions)

    @bp.get(
        "/studies/{uuid}/config/thematictrimming/form",
        summary="Get thematic trimming config",
        response_model_exclude_none=True,
    )
    def get_thematic_trimming(uuid: str) -> ThematicTrimming:
        logger.info(f"Fetching thematic trimming config for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
        study_interface = study_service.get_study_interface(study)
        return study_service.thematic_trimming_manager.get_thematic_trimming(study_interface)

    @bp.put(
        path="/studies/{uuid}/config/thematictrimming/form",
        summary="Set thematic trimming config",
    )
    def set_thematic_trimming(uuid: str, field_values: ThematicTrimmingUpdate) -> ThematicTrimming:
        logger.info(f"Updating thematic trimming config for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        return study_service.thematic_trimming_manager.update_thematic_trimming(study_interface, field_values)

    @bp.get(
        path="/studies/{uuid}/config/playlist/form",
        summary="Get MC Scenario playlist data for table form",
    )
    def get_playlist(uuid: str) -> PlaylistRootModel:
        logger.info(f"Getting MC Scenario playlist data for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
        study_interface = study_service.get_study_interface(study)
        playlist_as_dict = study_service.playlist_manager.get_playlist(study_interface).years
        return PlaylistRootModel.model_validate(playlist_as_dict)

    @bp.put(
        path="/studies/{uuid}/config/playlist/form",
        summary="Update MC Scenario playlist data with values from table form",
    )
    def update_playlist(uuid: str, data: PlaylistUpdateRootModel) -> PlaylistRootModel:
        logger.info(f"Updating MC Scenario playlist table data for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        playlist_update = PlaylistUpdate.model_validate({"years": data.model_dump()})
        playlist_as_dict = study_service.playlist_manager.update_playlist(study_interface, playlist_update).years
        return PlaylistRootModel.model_validate(playlist_as_dict)

    @bp.get(
        path="/studies/{uuid}/config/scenariobuilder",
        summary="Get MC Scenario builder config",
        response_model_exclude_none=True,
    )
    def get_scenario_builder_config(uuid: str) -> RulesetsView:
        logger.info(f"Getting MC Scenario builder config for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
        study_interface = study_service.get_study_interface(study)
        return rulesets_model_to_view(study_service.scenario_builder_manager.get_rulesets(study_interface))

    @bp.get(
        path="/studies/{uuid}/config/scenariobuilder/{scenario_type}",
        summary="Get MC Scenario builder config",
    )
    def get_scenario_builder_config_by_type(uuid: str, scenario_type: ScenarioType) -> Dict[str, AnyScenarios]:
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
        logger.info(f"Getting MC Scenario builder config for study {uuid} with scenario type filter: {scenario_type}")
        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
        study_interface = study_service.get_study_interface(study)
        table_form = study_service.scenario_builder_manager.get_scenario_by_type(study_interface, scenario_type)
        return {scenario_type: table_form}

    @bp.put(
        path="/studies/{uuid}/config/scenariobuilder",
        summary="Set MC Scenario builder config",
    )
    def update_scenario_builder_config(uuid: str, data: RulesetsView) -> None:
        logger.info(f"Updating MC Scenario builder config for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        study_service.scenario_builder_manager.update_scenario(study_interface, rulesets_view_to_model(data))

    @bp.put(
        path="/studies/{uuid}/config/scenariobuilder/{scenario_type}",
        summary="Set MC Scenario builder config",
    )
    def update_scenario_builder_config_by_type(
        uuid: str, scenario_type: ScenarioType, data: Dict[ScenarioType, AnyScenarios]
    ) -> Dict[ScenarioType, AnyScenarios]:
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
        logger.info(f"Updating MC Scenario builder config for study {uuid} with scenario type filter: {scenario_type}")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        table_form = data.get(scenario_type, {})
        table_form = study_service.scenario_builder_manager.update_scenario_by_type(
            study_interface, table_form, scenario_type
        )
        return {scenario_type: table_form}

    @bp.get(
        path="/studies/{uuid}/config/general/form",
        summary="Get General config values for form",
        response_model_exclude_none=True,
    )
    def get_general_form_values(uuid: str) -> GeneralConfig:
        logger.info(msg=f"Getting General management config for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
        study_interface = study_service.get_study_interface(study)
        return study_service.general_manager.get_general_config(study_interface)

    @bp.put(
        path="/studies/{uuid}/config/general/form",
        summary="Set General config with values from form",
    )
    def set_general_form_values(uuid: str, config: GeneralConfigUpdate) -> GeneralConfig:
        logger.info(f"Updating General management config for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        return study_service.general_manager.update_general_config(study_interface, config)

    @bp.get(
        path="/studies/{uuid}/config/optimization/form",
        summary="Get optimization config values for form",
    )
    def get_optimization_form_values(uuid: str) -> OptimizationPreferences:
        logger.info(msg=f"Getting optimization config for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
        study_interface = study_service.get_study_interface(study)
        return study_service.optimization_manager.get_optimization_preferences(study_interface)

    @bp.put(
        path="/studies/{uuid}/config/optimization/form",
        summary="Set optimization config with values from form",
    )
    def set_optimization_form_values(uuid: str, field_values: OptimizationPreferencesUpdate) -> OptimizationPreferences:
        logger.info(f"Updating optimization config for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        return study_service.optimization_manager.update_optimization_preferences(study_interface, field_values)

    @bp.get(
        path="/studies/{uuid}/config/adequacypatch/form",
        summary="Get adequacy patch config values for form",
        response_model_exclude_none=True,
    )
    def get_adequacy_patch_form_values(uuid: str) -> AdequacyPatchParameters:
        logger.info(msg=f"Getting adequacy patch config for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
        study_interface = study_service.get_study_interface(study)
        return study_service.adequacy_patch_manager.get_adequacy_patch_parameters(study_interface)

    @bp.put(
        path="/studies/{uuid}/config/adequacypatch/form",
        summary="Set adequacy patch config with values from form",
    )
    def set_adequacy_patch_form_values(
        uuid: str, field_values: AdequacyPatchParametersUpdate
    ) -> AdequacyPatchParameters:
        logger.info(f"Updating adequacy patch config for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        return study_service.adequacy_patch_manager.set_adequacy_patch_parameters(study_interface, field_values)

    @bp.get(
        path="/studies/{uuid}/timeseries/config",
        summary="Gets the TS Generation config",
        response_model_exclude_none=True,
    )
    def get_timeseries_form_values(uuid: str) -> TimeSeriesConfiguration:
        logger.info(msg=f"Getting Time-Series generation config for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
        study_interface = study_service.get_study_interface(study)
        return study_service.ts_config_manager.get_timeseries_configuration(study_interface)

    @bp.put(
        path="/studies/{uuid}/timeseries/config",
        summary="Sets the TS Generation config",
    )
    def set_ts_generation_config(uuid: str, field_values: TimeSeriesConfigurationUpdate) -> TimeSeriesConfiguration:
        logger.info(f"Updating Time-Series generation config for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        return study_service.ts_config_manager.set_timeseries_configuration(study_interface, field_values)

    @bp.get(
        path="/table-schema/{table_type}",
        summary="Get table schema",
    )
    def get_table_schema(table_type: TableModeType) -> JSON:
        """
        Get the properties of the table columns.

        Args:
        - `table_type`: The type of table to get the schema for.
        """
        logger.info("Getting table schema")
        model_schema = study_service.table_mode_manager.get_table_schema(table_type)
        return model_schema

    @bp.get(
        path="/studies/{uuid}/table-mode/{table_type}",
        summary="Get table data for table form",
    )
    def get_table_mode(
        uuid: str,
        table_type: TableModeType,
        columns: str = Query("", description="A comma-separated list of columns to include in the table data"),
    ) -> TableDataDTO:
        """
        Get the table data for the given study and table type.

        Args:
        - uuid: The UUID of the study.
        - table_type: The type of table to get the data for.
        """
        logger.info(f"Getting table data for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
        study_interface = study_service.get_study_interface(study)
        column_list = columns.split(",") if columns else []
        table_data = study_service.table_mode_manager.get_table_data(study_interface, table_type, column_list)
        return table_data

    @bp.put(
        path="/studies/{uuid}/table-mode/{table_type}",
        summary="Update table data with values from table form",
    )
    def update_table_mode(
        uuid: str,
        table_type: TableModeType,
        data: TableDataDTO = Body(
            ...,
            examples=[
                {
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
                }
            ],
        ),
    ) -> TableDataDTO:
        """
        Update the table data for the given study and table type.

        Args:
        - uuid: The UUID of the study.
        - table_type: The type of table to update.
        - data: The table data to update.
        """
        logger.info(f"Updating table data for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        table_data = study_service.table_mode_manager.update_table_data(study_interface, table_type, data)
        return table_data

    @bp.get("/studies/{uuid}/bindingconstraints", summary="Get binding constraint list")
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
    ) -> Sequence[BindingConstraint]:
        logger.info(f"Fetching binding constraint list for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
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
        summary="Get binding constraint",
    )
    def get_binding_constraint(uuid: str, binding_constraint_id: str) -> BindingConstraint:
        logger.info(f"Fetching binding constraint {binding_constraint_id} for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
        study_interface = study_service.get_study_interface(study)
        return study_service.binding_constraint_manager.get_binding_constraint(study_interface, binding_constraint_id)

    @bp.put(
        "/studies/{uuid}/bindingconstraints/{binding_constraint_id}",
        summary="Update binding constraint",
    )
    def update_binding_constraint(
        uuid: str, binding_constraint_id: str, data: BindingConstraintUpdateWithMatrices
    ) -> BindingConstraint:
        logger.info(f"Update binding constraint {binding_constraint_id} for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        return study_service.binding_constraint_manager.update_binding_constraint(
            study_interface, binding_constraint_id, data.update_model(), data.matrices()
        )

    @bp.get(
        "/studies/{uuid}/constraint-groups",
        summary="Get the list of binding constraint groups",
    )
    def get_grouped_constraints(uuid: str) -> Mapping[str, Sequence[BindingConstraint]]:
        """
        Get the list of binding constraint groups for the study.

        Args:
        - `uuid`: The UUID of the study.

        Returns:
        - The list of binding constraints for each group.
        """
        logger.info(f"Fetching binding constraint groups for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
        study_interface = study_service.get_study_interface(study)
        result = study_service.binding_constraint_manager.get_grouped_constraints(study_interface)
        return result

    @bp.get(
        # We use "validate-all" because it is unlikely to conflict with a group name.
        "/studies/{uuid}/constraint-groups/validate-all",
        summary="Validate all binding constraint groups",
    )
    def validate_constraint_groups(uuid: str) -> bool:
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
        logger.info(f"Validating all binding constraint groups for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
        study_interface = study_service.get_study_interface(study)
        return study_service.binding_constraint_manager.validate_constraint_groups(study_interface)

    @bp.get(
        "/studies/{uuid}/constraint-groups/{group}",
        summary="Get the binding constraint group",
    )
    def get_constraints_by_group(uuid: str, group: str) -> Sequence[BindingConstraint]:
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
        logger.info(f"Fetching binding constraint group '{group}' for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
        study_interface = study_service.get_study_interface(study)
        result = study_service.binding_constraint_manager.get_constraints_by_group(study_interface, group)
        return result

    @bp.get(
        "/studies/{uuid}/constraint-groups/{group}/validate",
        summary="Validate the binding constraint group",
    )
    def validate_constraint_group(uuid: str, group: str) -> bool:
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
        logger.info(f"Validating binding constraint group '{group}' for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
        study_interface = study_service.get_study_interface(study)
        return study_service.binding_constraint_manager.validate_constraint_group(study_interface, group)

    @bp.post("/studies/{uuid}/bindingconstraints", summary="Create a binding constraint")
    def create_binding_constraint(uuid: str, data: BindingConstraintCreationWithMatrices) -> BindingConstraint:
        logger.info(f"Creating a new binding constraint for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
        study_interface = study_service.get_study_interface(study)
        return study_service.binding_constraint_manager.create_binding_constraint(
            study_interface, data.creation_model(), data.matrices()
        )

    @bp.post(
        "/studies/{uuid}/bindingconstraints/{binding_constraint_id}",
        summary="Duplicates a given binding constraint",
    )
    def duplicate_binding_constraint(
        uuid: str, binding_constraint_id: str, new_constraint_name: str
    ) -> BindingConstraint:
        logger.info(f"Duplicates constraint {binding_constraint_id} for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        return study_service.binding_constraint_manager.duplicate_binding_constraint(
            study_interface, binding_constraint_id, new_constraint_name
        )

    @bp.delete(
        "/studies/{uuid}/bindingconstraints/{binding_constraint_id}",
        summary="Delete a binding constraint",
    )
    def delete_binding_constraint(uuid: str, binding_constraint_id: str) -> None:
        logger.info(f"Deleting the binding constraint {binding_constraint_id} for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        return study_service.binding_constraint_manager.remove_multiple_binding_constraints(
            study_interface, [binding_constraint_id]
        )

    @bp.delete(
        "/studies/{uuid}/bindingconstraints",
        summary="Delete multiple binding constraints",
    )
    def delete_multiple_binding_constraints(uuid: str, binding_constraints_ids: List[str]) -> None:
        logger.info(f"Deleting the binding constraints {binding_constraints_ids!r} for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        return study_service.binding_constraint_manager.remove_multiple_binding_constraints(
            study_interface, binding_constraints_ids
        )

    @bp.post(
        "/studies/{uuid}/bindingconstraints/{binding_constraint_id}/term",
        summary="Deprecated, please use PUT /bindingconstraints/<id> to modify the list of terms",
        deprecated=True,
    )
    def add_constraint_term(uuid: str, binding_constraint_id: str, term: ConstraintTerm) -> None:
        """
        Append a new term to a given binding constraint

        Args:
        - `uuid`: The UUID of the study.
        - `binding_constraint_id`: The binding constraint ID.
        - `term`: The term to create.
        """
        logger.info(f"Add constraint term {term.generate_id()} to {binding_constraint_id} for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        return study_service.binding_constraint_manager.add_constraint_terms(
            study_interface, binding_constraint_id, [term]
        )

    @bp.post(
        "/studies/{uuid}/bindingconstraints/{binding_constraint_id}/terms",
        summary="Deprecated, please use PUT /bindingconstraints/<id> to modify the list of terms",
        deprecated=True,
    )
    def add_constraint_terms(uuid: str, binding_constraint_id: str, terms: Sequence[ConstraintTerm]) -> None:
        """
        Append new terms to a given binding constraint

        Args:
        - `uuid`: The UUID of the study.
        - `binding_constraint_id`: The binding constraint ID.
        - `terms`: The list of terms to create.
        """
        logger.info(f"Adding constraint terms to {binding_constraint_id} for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        return study_service.binding_constraint_manager.add_constraint_terms(
            study_interface, binding_constraint_id, terms
        )

    @bp.put(
        "/studies/{uuid}/bindingconstraints/{binding_constraint_id}/term",
        summary="Deprecated, please use PUT /bindingconstraints/<id> to modify the list of terms",
        deprecated=True,
    )
    def update_constraint_term(uuid: str, binding_constraint_id: str, term: ConstraintTermUpdate) -> None:
        """
        Update a term for a given binding constraint

        Args:
        - `uuid`: The UUID of the study.
        - `binding_constraint_id`: The binding constraint ID.
        - `term`: The term to update.
        """
        logger.info(f"Update constraint term {term.id} from {binding_constraint_id} for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        return study_service.binding_constraint_manager.update_constraint_terms(
            study_interface, binding_constraint_id, [term]
        )

    @bp.put(
        "/studies/{uuid}/bindingconstraints/{binding_constraint_id}/terms",
        summary="Deprecated, please use PUT /bindingconstraints/<id> to modify the list of terms",
        deprecated=True,
    )
    def update_constraint_terms(uuid: str, binding_constraint_id: str, terms: Sequence[ConstraintTermUpdate]) -> None:
        """
        Update several terms for a given binding constraint

        Args:
        - `uuid`: The UUID of the study.
        - `binding_constraint_id`: The binding constraint ID.
        - `terms`: The list of terms to update.
        """
        logger.info(f"Updating constraint terms from {binding_constraint_id} for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        return study_service.binding_constraint_manager.update_constraint_terms(
            study_interface, binding_constraint_id, terms
        )

    @bp.delete(
        "/studies/{uuid}/bindingconstraints/{binding_constraint_id}/term/{term_id}",
        summary="Deprecated, please use PUT /bindingconstraints/<id> to modify the list of terms",
        deprecated=True,
    )
    def remove_constraint_term(uuid: str, binding_constraint_id: str, term_id: str) -> None:
        logger.info(f"Remove constraint term {term_id} from {binding_constraint_id} for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        study_service.binding_constraint_manager.remove_constraint_term(study_interface, binding_constraint_id, term_id)

    @bp.get(
        path="/studies/{uuid}/areas/hydro/allocation/matrix",
        summary="Get the hydraulic allocation matrix for all areas",
    )
    def get_allocation_matrix(uuid: str) -> HydroAllocationMatrix:
        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
        study_interface = study_service.get_study_interface(study)
        return study_service.allocation_manager.get_allocation_matrix(study_interface)

    @bp.get(
        path="/studies/{uuid}/areas/{area_id}/hydro/allocation/form",
        summary="Get the form fields used for the allocation form",
    )
    def get_allocation_form_fields(uuid: str, area_id: str) -> HydroAllocation:
        """
        Get the form fields used for the allocation form.

        Args:
        - `uuid`: The study UUID,
        - `area_id`: the area ID.

        Returns the allocation form fields.
        """
        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
        study_interface = study_service.get_study_interface(study)
        return study_service.allocation_manager.get_allocation_for_area(study_interface, area_id)

    @bp.put(
        path="/studies/{uuid}/areas/{area_id}/hydro/allocation/form",
        summary="Update the form fields used for the allocation form",
        status_code=HTTPStatus.OK,
    )
    def set_allocation_form_fields(
        uuid: str,
        area_id: str,
        data: HydroAllocation = Body(
            ...,
            examples=[
                HydroAllocation(
                    allocation=[
                        HydroAllocationArea.model_validate({"areaId": "EAST", "coefficient": 1}),
                        HydroAllocationArea.model_validate({"areaId": "NORTH", "coefficient": 0.20}),
                    ]
                )
            ],
        ),
    ) -> HydroAllocation:
        """
        Update the hydraulic allocation of a given area.

        Args:
        - `uuid`: The study UUID,
        - `area_id`: the area ID.

        Returns the updated allocation form fields.
        """
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        return study_service.allocation_manager.set_allocation_for_area(study_interface, area_id, data)

    @bp.get(
        path="/studies/{uuid}/areas/hydro/correlation/matrix",
        summary="Get the hydraulic correlation matrix of a study",
    )
    def get_correlation_matrix(uuid: str) -> HydroCorrelationMatrix:
        """
        Get the hydraulic correlation matrix of a study.

        Args:
        - `uuid`: The UUID of the study.

        Returns the hydraulic/load/solar/wind correlation matrix with the following attributes:
        - `index`: a list of all study areas.
        - `columns`: a list of selected production areas.
        - `data`: a 2D-array matrix of correlation coefficients with values in the range of -1 to 1.
        """
        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
        study_interface = study_service.get_study_interface(study)
        return study_service.correlation_manager.get_correlation_matrix(study_interface)

    @bp.get(
        path="/studies/{uuid}/areas/{area_id}/hydro/correlation/form",
        summary="Get the form fields used for the correlation form",
    )
    def get_correlation(uuid: str, area_id: str) -> HydroCorrelation:
        """
        Get the form fields used for the correlation form.

        Args:
        - `uuid`: The UUID of the study.
        - `area_id`: the area ID.

        Returns the correlation form fields in percentage.
        """
        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
        study_interface = study_service.get_study_interface(study)
        return study_service.correlation_manager.get_correlation_for_area(study_interface, area_id)

    @bp.put(
        path="/studies/{uuid}/areas/{area_id}/hydro/correlation/form",
        summary="Set the form fields used for the correlation form",
        status_code=HTTPStatus.OK,
    )
    def set_correlation(
        uuid: str,
        area_id: str,
        data: HydroCorrelation = Body(
            ...,
            examples=[
                HydroCorrelation(
                    correlation=[
                        HydroCorrelationArea.model_validate({"areaId": "east", "coefficient": 80}),
                        HydroCorrelationArea.model_validate({"areaId": "north", "coefficient": 20}),
                    ]
                )
            ],
        ),
    ) -> HydroCorrelation:
        """
        Update the hydraulic correlation of a given area.

        Args:
        - `uuid`: The UUID of the study.
        - `area_id`: the area ID.

        Returns the correlation form fields in percentage.
        """
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        return study_service.correlation_manager.set_correlation_for_area(study_interface, area_id, data)

    @bp.get(
        path="/studies/{uuid}/config/advancedparameters/form",
        summary="Get Advanced parameters form values",
        response_model_exclude_none=True,
    )
    def get_advanced_parameters(uuid: str) -> AdvancedParameters:
        logger.info(msg=f"Getting Advanced Parameters for study {uuid}")

        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
        study_interface = study_service.get_study_interface(study)
        return study_service.advanced_parameters_manager.get_advanced_parameters(study_interface)

    @bp.put(
        path="/studies/{uuid}/config/advancedparameters/form",
        summary="Set Advanced parameters new values",
    )
    def set_advanced_parameters(uuid: str, field_values: AdvancedParametersUpdate) -> AdvancedParameters:
        logger.info(f"Updating Advanced parameters values for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        return study_service.advanced_parameters_manager.update_advanced_parameters(study_interface, field_values)

    # Compatibility parameters
    @bp.get(
        path="/studies/{uuid}/config/compatibility/form",
        summary="Get Compatibility parameters form values",
        response_model_exclude_none=True,
    )
    def get_compatibility_parameters(uuid: str) -> CompatibilityParameters:
        logger.info(msg=f"Getting Compatibility Parameters for study {uuid}")

        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
        study_interface = study_service.get_study_interface(study)
        return study_service.compatibility_parameters_manager.get_compatibility_parameters(study_interface)

    @bp.put(
        path="/studies/{uuid}/config/compatibility/form",
        summary="Set Compatibility parameters new values",
    )
    def set_compatibility_parameters(uuid: str, field_values: CompatibilityParametersUpdate) -> CompatibilityParameters:
        logger.info(f"Updating Compatibility parameters values for study {uuid}")
        """
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        return study_service.compatibility_parameters_manager.update_compatibility_parameters(study_interface, field_values)
        """
        pass

    # To this

    @bp.put(
        "/studies/{uuid}/timeseries/generate",
        summary="Generate timeseries",
    )
    def generate_timeseries(uuid: str, outage_details: bool = Query(default=False)) -> str:
        """
        Generates time-series for thermal clusters and put them inside input data.

        Args:
        - `uuid`: The UUID of the study.
        - `outage_details`: Whether to generate thermal outage details.
        """
        logger.info(f"Generating timeseries for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        return study_service.generate_timeseries(study, outage_details)

    @bp.get(
        path="/studies/{uuid}/areas/{area_id}/properties/form",
        summary="Get properties for a given area",
        response_model_exclude_none=True,
    )
    def get_properties_form_values(uuid: str, area_id: str) -> AreaProperties:
        logger.info("Getting properties form values for study %s and area %s", uuid, area_id)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
        study_interface = study_service.get_study_interface(study)
        return study_service.area_manager.get_area_properties(study_interface, area_id)

    @bp.put(
        path="/studies/{uuid}/areas/{area_id}/properties/form",
        summary="Set properties for a given area",
    )
    def set_properties_form_values(uuid: str, area_id: str, form_fields: AreaPropertiesUpdate) -> None:
        logger.info("Setting properties form values for study %s and area %s", uuid, area_id)
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        study_service.area_manager.update_all_area_properties(
            study_interface,
            {area_id: form_fields},
        )

    @bp.get(
        path="/studies/{uuid}/areas/{area_id}/clusters/renewable",
        summary="Get all renewable clusters",
    )
    def get_renewable_clusters(uuid: str, area_id: str) -> Sequence[RenewableCluster]:
        logger.info("Getting renewable clusters for study %s and area %s", uuid, area_id)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
        study_interface = study_service.get_study_interface(study)
        return study_service.renewable_manager.get_clusters(study_interface, area_id)

    @bp.get(
        path="/studies/{uuid}/areas/{area_id}/clusters/renewable/{cluster_id}",
        summary="Get a single renewable cluster",
    )
    def get_renewable_cluster(uuid: str, area_id: str, cluster_id: str) -> RenewableCluster:
        logger.info("Getting renewable cluster values for study %s and cluster %s", uuid, cluster_id)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
        study_interface = study_service.get_study_interface(study)
        return study_service.renewable_manager.get_cluster(study_interface, area_id, cluster_id)

    @bp.get(
        path="/studies/{uuid}/areas/{area_id}/clusters/renewable/{cluster_id}/form",
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
        summary="Create a new renewable cluster",
    )
    def create_renewable_cluster(uuid: str, area_id: str, cluster_data: RenewableClusterCreation) -> RenewableCluster:
        """
        Create a new renewable cluster.

        Args:
        - `uuid`: The UUID of the study.
        - `area_id`: the area ID.
        - `cluster_data`: the properties used for creation:
          "name" and "group".

        Returns: The properties of the newly-created renewable cluster.
        """
        logger.info(f"Creating renewable cluster for study '{uuid}' and area '{area_id}'")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        return study_service.renewable_manager.create_cluster(study_interface, area_id, cluster_data)

    @bp.patch(
        path="/studies/{uuid}/areas/{area_id}/clusters/renewable/{cluster_id}",
        summary="Update a renewable cluster",
    )
    def update_renewable_cluster(
        uuid: str, area_id: str, cluster_id: str, cluster_data: RenewableClusterUpdate
    ) -> RenewableCluster:
        logger.info(f"Updating renewable cluster for study '{uuid}' and cluster '{cluster_id}'")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        return study_service.renewable_manager.update_cluster(study_interface, area_id, cluster_id, cluster_data)

    @bp.put(
        path="/studies/{uuid}/areas/{area_id}/clusters/renewable/{cluster_id}/form",
        summary="Get renewable configuration for a given cluster (deprecated)",
        deprecated=True,
    )
    def redirect_update_renewable_cluster(
        uuid: str, area_id: str, cluster_id: str, cluster_data: RenewableClusterUpdate
    ) -> RenewableCluster:
        # We cannot perform redirection, because we have a PUT, where a PATCH is required.
        return update_renewable_cluster(uuid, area_id, cluster_id, cluster_data)

    @bp.delete(
        path="/studies/{uuid}/areas/{area_id}/clusters/renewable",
        summary="Remove renewable clusters",
        status_code=HTTPStatus.NO_CONTENT,
    )
    def delete_renewable_clusters(uuid: str, area_id: str, cluster_ids: Sequence[str]) -> None:
        """
        Remove one or several renewable cluster(s) and it's time series.

        Args:
        - `uuid`: The UUID of the study.
        - `area_id`: the area ID.
        - `cluster_ids`: list of IDs to remove.
        """
        logger.info(f"Deleting renewable clusters {cluster_ids!r} for study '{uuid}' and area '{area_id}'")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        study_service.renewable_manager.delete_clusters(study_interface, area_id, cluster_ids)

    @bp.get(
        path="/studies/{uuid}/areas/{area_id}/clusters/thermal",
        summary="Get thermal clusters for a given area",
    )
    def get_thermal_clusters(uuid: str, area_id: str) -> Sequence[ThermalCluster]:
        """
        Retrieve the list of thermal clusters for a specified area.

        Args:
        - `uuid`: The UUID of the study.
        - `area_id`: the area ID.

        Returns: The list thermal clusters.
        """
        logger.info("Getting thermal clusters for study %s and area %s", uuid, area_id)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
        study_interface = study_service.get_study_interface(study)
        return study_service.thermal_manager.get_clusters(study_interface, area_id)

    @bp.get(
        path="/studies/{uuid}/areas/{area_id}/clusters/thermal/{cluster_id}",
        summary="Get thermal configuration for a given cluster",
    )
    def get_thermal_cluster(uuid: str, area_id: str, cluster_id: str) -> ThermalCluster:
        """
        Retrieve the thermal clusters for a specified area.

        Args:
        - `uuid`: The UUID of the study.
        - `area_id`: the area ID.
        - `cluster_id`: the cluster ID.

        Returns: The properties of the thermal clusters.
        """
        logger.info("Getting thermal cluster values for study %s and cluster %s", uuid, cluster_id)
        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
        study_interface = study_service.get_study_interface(study)
        return study_service.thermal_manager.get_cluster(study_interface, area_id, cluster_id)

    @bp.get(
        path="/studies/{uuid}/areas/{area_id}/clusters/thermal/{cluster_id}/form",
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
        summary="Create a new thermal cluster for a given area",
    )
    def create_thermal_cluster(uuid: str, area_id: str, cluster_data: ThermalClusterCreation) -> ThermalCluster:
        """
        Create a new thermal cluster for a specified area.

        Args:
        - `uuid`: The UUID of the study.
        - `area_id`: the area ID.
        - `cluster_data`: the properties used for creation:
          "name" and "group".

        Returns: The properties of the newly-created thermal cluster.
        """
        logger.info(f"Creating thermal cluster for study '{uuid}' and area '{area_id}'")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        return study_service.thermal_manager.create_cluster(study_interface, area_id, cluster_data)

    @bp.patch(
        path="/studies/{uuid}/areas/{area_id}/clusters/thermal/{cluster_id}",
        summary="Update thermal cluster for a given area",
    )
    def update_thermal_cluster(
        uuid: str, area_id: str, cluster_id: str, cluster_data: ThermalClusterUpdate
    ) -> ThermalCluster:
        """
        Update the properties of a thermal cluster for a specified area.

        Args:
        - `uuid`: The UUID of the study.
        - `area_id`: the area ID.
        - `cluster_data`: the properties used for updating.

        Returns: The properties of the updated thermal clusters.
        """
        logger.info(f"Updating thermal cluster for study '{uuid}' and cluster '{cluster_id}'")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        return study_service.thermal_manager.update_cluster(study_interface, area_id, cluster_id, cluster_data)

    @bp.put(
        path="/studies/{uuid}/areas/{area_id}/clusters/thermal/{cluster_id}/form",
        summary="Get thermal configuration for a given cluster (deprecated)",
        deprecated=True,
    )
    def redirect_update_thermal_cluster(
        uuid: str, area_id: str, cluster_id: str, cluster_data: ThermalClusterUpdate
    ) -> ThermalCluster:
        # We cannot perform redirection, because we have a PUT, where a PATCH is required.
        return update_thermal_cluster(uuid, area_id, cluster_id, cluster_data)

    @bp.delete(
        path="/studies/{uuid}/areas/{area_id}/clusters/thermal",
        summary="Remove thermal clusters for a given area",
        status_code=HTTPStatus.NO_CONTENT,
    )
    def delete_thermal_clusters(uuid: str, area_id: str, cluster_ids: Sequence[str]) -> None:
        """
        Remove one or several thermal cluster(s) from a specified area.
        This endpoint removes the properties and time series of each thermal clusters.

        Args:
        - `uuid`: The UUID of the study.
        - `area_id`: the area ID.
        - `cluster_ids`: list of thermal cluster IDs to remove.
        """
        logger.info(f"Deleting thermal clusters {cluster_ids!r} for study '{uuid}' and area '{area_id}'")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        study_service.asserts_no_thermal_in_binding_constraints(study, area_id, cluster_ids)
        study_service.thermal_manager.delete_clusters(study_interface, area_id, cluster_ids)

    @bp.get(
        path="/studies/{uuid}/areas/{area_id}/storages/{storage_id}",
        summary="Get the short-term storage properties",
    )
    def get_st_storage(uuid: str, area_id: str, storage_id: str) -> STStorage:
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
        logger.info(f"Getting values for study {uuid} and short term storage {storage_id}")
        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
        study_interface = study_service.get_study_interface(study)
        return study_service.st_storage_manager.get_storage(study_interface, area_id, storage_id)

    @bp.get(
        path="/studies/{uuid}/areas/{area_id}/storages",
        summary="Get the list of short-term storage properties",
    )
    def get_st_storages(uuid: str, area_id: str) -> Sequence[STStorage]:
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
        logger.info(f"Getting storages for study {uuid} in a given area {area_id}")
        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
        study_interface = study_service.get_study_interface(study)
        return study_service.st_storage_manager.get_storages(study_interface, area_id)

    @bp.post(
        path="/studies/{uuid}/areas/{area_id}/storages",
        summary="Create a new short-term storage in an area",
    )
    def create_st_storage(uuid: str, area_id: str, form: STStorageCreation) -> STStorage:
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

        logger.info(f"Create short-term storage from {area_id} for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        return study_service.st_storage_manager.create_storage(study_interface, area_id, form)

    @bp.patch(
        path="/studies/{uuid}/areas/{area_id}/storages/{storage_id}",
        summary="Update the short-term storage properties",
    )
    def update_st_storage(uuid: str, area_id: str, storage_id: str, form: STStorageUpdate) -> STStorage:
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

        logger.info(f"Update short-term storage {storage_id} from {area_id} for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        return study_service.st_storage_manager.update_storage(study_interface, area_id, storage_id, form)

    @bp.delete(
        path="/studies/{uuid}/areas/{area_id}/storages",
        summary="Remove short-term storages from an area",
        status_code=HTTPStatus.NO_CONTENT,
    )
    def delete_st_storages(uuid: str, area_id: str, storage_ids: Sequence[str]) -> None:
        """
        Delete short-term storages from an area.

        Args:
        - `uuid`: The UUID of the study.
        - `area_id`: the area ID.
        - `storage_ids`: ist of IDs of the storages to remove from the area.

        Permissions:
        - User must have DELETED permission on the study.
        """
        logger.info(f"Delete short-term storage ID's {storage_ids} from {area_id} for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        study_service.st_storage_manager.delete_storages(study_interface, area_id, storage_ids)

    @bp.get(
        path="/studies/{uuid}/areas/{area_id}/storages/{storage_id}/additional-constraints",
        summary="Get all additional constraints relative to a short-term storage object",
    )
    def get_additional_constraints(uuid: str, area_id: str, storage_id: str) -> list[STStorageAdditionalConstraint]:
        logger.info(f"Getting additional constraints for short-term storage {storage_id} in {area_id} for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
        study_interface = study_service.get_study_interface(study)
        return study_service.st_storage_manager.get_additional_constraints(study_interface, area_id, storage_id)

    @bp.get(
        path="/studies/{uuid}/areas/{area_id}/storages/{storage_id}/additional-constraints/{constraint_id}",
        summary="Get a specific constraint relative to a short-term storage object",
    )
    def get_additional_constraint(
        uuid: str, area_id: str, storage_id: str, constraint_id: str
    ) -> STStorageAdditionalConstraint:
        logger.info(
            f"Getting additional constraint {constraint_id} for short-term storage {storage_id} in {area_id} for study {uuid}"
        )
        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
        study_interface = study_service.get_study_interface(study)
        return study_service.st_storage_manager.get_additional_constraint(
            study_interface, area_id, storage_id, constraint_id
        )

    @bp.post(
        path="/studies/{uuid}/areas/{area_id}/storages/{storage_id}/additional-constraints",
        summary="Create additional constraint(s) for a short-term storage object",
    )
    def create_additional_constraints(
        uuid: str, area_id: str, storage_id: str, constraints: list[STStorageAdditionalConstraintCreation]
    ) -> list[STStorageAdditionalConstraint]:
        logger.info(
            f"Creating additional constraint(s) for short-term storage {storage_id} in {area_id} for study {uuid}"
        )
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        return study_service.st_storage_manager.create_additional_constraints(
            study_interface, area_id, storage_id, constraints
        )

    @bp.put(
        path="/studies/{uuid}/areas/{area_id}/storages/{storage_id}/additional-constraints",
        summary="Update additional constraint(s) for a short-term storage object",
    )
    def update_additional_constraints(
        uuid: str, area_id: str, storage_id: str, constraints: dict[str, STStorageAdditionalConstraintUpdate]
    ) -> list[STStorageAdditionalConstraint]:
        logger.info(
            f"Updating additional constraint(s) for short-term storage {storage_id} in {area_id} for study {uuid}"
        )
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        all_constraints = study_service.st_storage_manager.update_additional_constraints(
            study_interface, {area_id: {storage_id: constraints}}
        )
        return all_constraints[area_id][storage_id]

    @bp.delete(
        path="/studies/{uuid}/areas/{area_id}/storages/{storage_id}/additional-constraints",
        summary="Delete additional constraint(s) for a given area",
    )
    def delete_additional_constraints(uuid: str, area_id: str, storage_id: str, constraints_ids: list[str]) -> None:
        logger.info(
            f"Deleting short-term storage additional constraint(s) for storage {storage_id} in area {area_id} for study {uuid}"
        )
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        study_service.st_storage_manager.delete_additional_constraints(
            study_interface, area_id, storage_id, constraints_ids
        )

    @bp.post(
        path="/studies/{uuid}/areas/{area_id}/{cluster_type}/{source_cluster_id}",
        summary="Duplicates a given cluster",
    )
    def duplicate_cluster(
        uuid: str,
        area_id: str,
        cluster_type: ClusterType,
        source_cluster_id: str,
        new_cluster_name: str = Query(..., alias="newName", title="New Cluster Name"),
    ) -> STStorage | ThermalCluster | RenewableCluster:
        logger.info(f"Duplicates {cluster_type.value} {source_cluster_id} of {area_id} for study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)

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

    @bp.get(
        "/studies/{study_id}/data",
        summary="Fetches data for the whole study",
        response_model_exclude_none=True,
    )
    def get_study_data(study_id: str) -> StudyDataDTO:
        """
        NOTE: This endpoint is used by antares-craft to read a study.
        """
        study_id = sanitize_uuid(study_id)
        return study_service.get_study_data(study_id)

    return bp
