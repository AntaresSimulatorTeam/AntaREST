import logging
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Body, Depends

from antarest.core.config import Config
from antarest.core.jwt import JWTUser
from antarest.core.model import StudyPermissionType
from antarest.core.requests import RequestParameters
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth
from antarest.matrixstore.business.matrix_editor import (
    MatrixEditInstructionDTO,
)
from antarest.study.business.advanced_parameters_management import (
    AdvancedParamsFormFields,
)
from antarest.study.business.area_management import (
    AreaCreationDTO,
    AreaInfoDTO,
    AreaType,
    AreaUI,
    LayerInfoDTO,
)
from antarest.study.business.binding_constraint_management import (
    ConstraintTermDTO,
    UpdateBindingConstProps,
)
from antarest.study.business.district_manager import DistrictDTO
from antarest.study.business.general_management import GeneralFormFields
from antarest.study.business.hydro_management import (
    ManagementOptionsFormFields,
)
from antarest.study.business.link_management import LinkInfoDTO
from antarest.study.business.optimization_management import (
    OptimizationFormFields,
)
from antarest.study.business.playlist_management import PlaylistColumns
from antarest.study.business.table_mode_management import (
    ColumnModelTypes,
    TableTemplateType,
)
from antarest.study.business.thematic_trimming_management import (
    ThematicTrimmingFormFields,
)
from antarest.study.business.timeseries_config_management import TSFormFields
from antarest.study.model import PatchArea, PatchCluster
from antarest.study.service import StudyService

logger = logging.getLogger(__name__)


def create_study_data_routes(
    study_service: StudyService, config: Config
) -> APIRouter:
    """
    Endpoint implementation for studies area management
    Args:
        study_service: study service facade to handle request
        config: main server configuration

    Returns:

    """
    bp = APIRouter(prefix="/v1")
    auth = Auth(config)

    @bp.get(
        "/studies/{uuid}/areas",
        tags=[APITag.study_data],
        summary="Get all areas basic info",
        response_model=Union[List[AreaInfoDTO], Dict[str, Any]],  # type: ignore
    )
    def get_areas(
        uuid: str,
        type: Optional[AreaType] = None,
        ui: bool = False,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Union[List[AreaInfoDTO], Dict[str, Any]]:
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
        response_model=List[LinkInfoDTO],
    )
    def get_links(
        uuid: str,
        with_ui: bool = False,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Fetching link list for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        areas_list = study_service.get_all_links(uuid, with_ui, params)
        return areas_list

    @bp.post(
        "/studies/{uuid}/areas",
        tags=[APITag.study_data],
        summary="Create a new area/cluster",
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
        response_model=LinkInfoDTO,
    )
    def create_link(
        uuid: str,
        link_creation_info: LinkInfoDTO,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Creating new link for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        return study_service.create_link(uuid, link_creation_info, params)

    @bp.put(
        "/studies/{uuid}/areas/{area_id}/ui",
        tags=[APITag.study_data],
        summary="Update area information",
        response_model=AreaInfoDTO,
    )
    def update_area_ui(
        uuid: str,
        area_id: str,
        area_ui: AreaUI,
        layer: str = "0",
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Updating area ui {area_id} for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        return study_service.update_area_ui(
            uuid, area_id, area_ui, layer, params
        )

    @bp.put(
        "/studies/{uuid}/areas/{area_id}",
        tags=[APITag.study_data],
        summary="Update area information",
        response_model=AreaInfoDTO,
    )
    def update_area_info(
        uuid: str,
        area_id: str,
        area_patch_dto: Union[PatchArea, Dict[str, PatchCluster]],
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Updating area {area_id} for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        if isinstance(area_patch_dto, PatchArea):
            return study_service.update_area(
                uuid, area_id, area_patch_dto, params
            )
        else:
            return study_service.update_thermal_cluster_metadata(
                uuid,
                area_id,
                area_patch_dto,
                params,
            )

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
        study = study_service.check_study_access(
            uuid, StudyPermissionType.READ, params
        )
        return study_service.areas.get_layers(study)

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
        study = study_service.check_study_access(
            uuid, StudyPermissionType.WRITE, params
        )
        return study_service.areas.create_layer(study, name)

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
        study = study_service.check_study_access(
            uuid, StudyPermissionType.READ, params
        )
        if name:
            study_service.areas.update_layer_name(study, layer_id, name)
        if areas:
            study_service.areas.update_layer_areas(study, layer_id, areas)

    @bp.delete(
        "/studies/{uuid}/layers/{layer_id}",
        tags=[APITag.study_data],
        summary="Remove layer",
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
        study = study_service.check_study_access(
            uuid, StudyPermissionType.READ, params
        )
        return study_service.areas.remove_layer(study, layer_id)

    @bp.get(
        "/studies/{uuid}/districts",
        tags=[APITag.study_data],
        summary="Get all districts info",
        response_model=List[DistrictDTO],
    )
    def get_districts(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> List[DistrictDTO]:
        logger.info(
            f"Fetching districts list for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(
            uuid, StudyPermissionType.READ, params
        )
        return study_service.district_manager.get_districts(study)

    @bp.post(
        "/studies/{uuid}/districts",
        tags=[APITag.study_data],
        summary="Create new district",
        response_model=str,
    )
    def create_district(
        uuid: str,
        name: str,
        output: bool,
        comments: str = "",
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> None:
        logger.info(
            f"Create district {name} for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(
            uuid, StudyPermissionType.WRITE, params
        )
        study_service.district_manager.create_district(
            study, name, output, comments
        )

    @bp.get(
        "/studies/{uuid}/areas/{area_id}/hydro/form",
        tags=[APITag.study_data],
        summary="Get Hydro config values for form",
        response_model=ManagementOptionsFormFields,
        response_model_exclude_none=True,
    )
    def get_hydro_form_values(
        uuid: str,
        area_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> ManagementOptionsFormFields:
        logger.info(
            msg=f"Getting Hydro management config for area {area_id} of study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(
            uuid, StudyPermissionType.READ, params
        )

        return study_service.hydro_manager.get_field_values(study, area_id)

    @bp.put(
        "/studies/{uuid}/areas/{area_id}/hydro/form",
        tags=[APITag.study_data],
        summary="Set Hydro config with values from form",
    )
    def set_hydro_form_values(
        uuid: str,
        area_id: str,
        data: ManagementOptionsFormFields,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            msg=f"Updating Hydro management config for area {area_id} of study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(
            uuid, StudyPermissionType.WRITE, params
        )

        return study_service.hydro_manager.set_field_values(
            study, data, area_id
        )

    @bp.put(
        "/studies/{uuid}/matrix",
        tags=[APITag.study_data],
        summary="Edit matrix",
    )
    def edit_matrix(
        uuid: str,
        path: str,
        matrix_edit_instructions: List[MatrixEditInstructionDTO] = Body(...),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        params = RequestParameters(user=current_user)
        study_service.update_matrix(
            uuid, path, matrix_edit_instructions, params
        )

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
        study = study_service.check_study_access(
            uuid, StudyPermissionType.READ, params
        )
        return study_service.thematic_trimming_manager.get_field_values(study)

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
        study = study_service.check_study_access(
            uuid, StudyPermissionType.WRITE, params
        )
        study_service.thematic_trimming_manager.set_field_values(
            study, field_values
        )

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
        study = study_service.check_study_access(
            uuid, StudyPermissionType.READ, params
        )

        return study_service.playlist_manager.get_table_data(study)

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
        study = study_service.check_study_access(
            uuid, StudyPermissionType.WRITE, params
        )
        study_service.playlist_manager.set_table_data(study, data)

    @bp.get(
        "/studies/{uuid}/config/playlist",
        tags=[APITag.study_data],
        summary="Get playlist config",
        response_model=Dict[int, float],
    )
    def get_playlist_config(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Fetching playlist config for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(
            uuid, StudyPermissionType.READ, params
        )
        return study_service.config_manager.get_playlist(study)

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
        study = study_service.check_study_access(
            uuid, StudyPermissionType.WRITE, params
        )
        study_service.config_manager.set_playlist(
            study, playlist, weights, reverse, active
        )

    @bp.get(
        path="/studies/{uuid}/config/scenariobuilder",
        tags=[APITag.study_data],
        summary="Get MC Scenario builder config",
        response_model=Dict[str, Any],
    )
    def get_scenario_builder_config(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Dict[str, Any]:
        logger.info(
            f"Getting MC Scenario builder config for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(
            uuid, StudyPermissionType.READ, params
        )

        return study_service.scenario_builder_manager.get_config(study)

    @bp.put(
        path="/studies/{uuid}/config/scenariobuilder",
        tags=[APITag.study_data],
        summary="Set MC Scenario builder config",
    )
    def update_scenario_builder_config(
        uuid: str,
        data: Dict[str, Any],
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> None:
        logger.info(
            f"Updating MC Scenario builder config for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(
            uuid, StudyPermissionType.WRITE, params
        )
        study_service.scenario_builder_manager.update_config(study, data)

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
        study = study_service.check_study_access(
            uuid, StudyPermissionType.READ, params
        )

        return study_service.general_manager.get_field_values(study)

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
        study = study_service.check_study_access(
            uuid, StudyPermissionType.WRITE, params
        )

        study_service.general_manager.set_field_values(study, field_values)

    @bp.get(
        path="/studies/{uuid}/config/optimization/form",
        tags=[APITag.study_data],
        summary="Get Optimization config values for form",
        response_model=OptimizationFormFields,
        response_model_exclude_none=True,
    )
    def get_optimization_form_values(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> OptimizationFormFields:
        logger.info(
            msg=f"Getting Optimization management config for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(
            uuid, StudyPermissionType.READ, params
        )

        return study_service.optimization_manager.get_field_values(study)

    @bp.put(
        path="/studies/{uuid}/config/optimization/form",
        tags=[APITag.study_data],
        summary="Set Optimization config with values from form",
    )
    def set_optimization_form_values(
        uuid: str,
        field_values: OptimizationFormFields,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> None:
        logger.info(
            f"Updating Optimization management config for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(
            uuid, StudyPermissionType.WRITE, params
        )

        study_service.optimization_manager.set_field_values(
            study, field_values
        )

    @bp.get(
        path="/studies/{uuid}/config/timeseries/form",
        tags=[APITag.study_data],
        summary="Get Time Series config values for form",
        response_model=TSFormFields,
        response_model_exclude_none=True,
    )
    def get_timeseries_form_values(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> TSFormFields:
        logger.info(
            msg=f"Getting Time Series config for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(
            uuid, StudyPermissionType.READ, params
        )

        return study_service.ts_config_manager.get_field_values(study)

    @bp.put(
        path="/studies/{uuid}/config/timeseries/form",
        tags=[APITag.study_data],
        summary="Set Time Series config with values from form",
    )
    def set_timeseries_form_values(
        uuid: str,
        field_values: TSFormFields,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> None:
        logger.info(
            f"Updating Time Series config for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(
            uuid, StudyPermissionType.WRITE, params
        )

        study_service.ts_config_manager.set_field_values(study, field_values)

    @bp.get(
        path="/studies/{uuid}/tablemode/form",
        tags=[APITag.study_data],
        summary="Get table data for table form",
        # `Any` because `Union[AreaColumns, LinkColumns]` not working
        response_model=Dict[str, Dict[str, Any]],
        response_model_exclude_none=True,
    )
    def get_table_data(
        uuid: str,
        table_type: TableTemplateType,
        columns: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Dict[str, ColumnModelTypes]:
        logger.info(
            f"Getting template table data for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(
            uuid, StudyPermissionType.READ, params
        )

        return study_service.table_mode_manager.get_table_data(
            study, table_type, columns.split(",")
        )

    @bp.put(
        path="/studies/{uuid}/tablemode/form",
        tags=[APITag.study_data],
        summary="Set table data with values from table form",
    )
    def set_table_data(
        uuid: str,
        table_type: TableTemplateType,
        data: Dict[str, ColumnModelTypes],
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> None:
        logger.info(
            f"Updating table data for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(
            uuid, StudyPermissionType.WRITE, params
        )

        study_service.table_mode_manager.set_table_data(
            study, table_type, data
        )

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
        response_model=None,  # Dict[str, bool],
    )
    def get_binding_constraint_list(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Fetching binding constraint list for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(
            uuid, StudyPermissionType.READ, params
        )
        return study_service.binding_constraint_manager.get_binding_constraint(
            study, None
        )

    @bp.get(
        "/studies/{uuid}/bindingconstraints/{binding_constraint_id}",
        tags=[APITag.study_data],
        summary="Get binding constraint list",
        response_model=None,  # Dict[str, bool],
    )
    def get_binding_constraint(
        uuid: str,
        binding_constraint_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Fetching binding constraint {binding_constraint_id} for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(
            uuid, StudyPermissionType.READ, params
        )
        return study_service.binding_constraint_manager.get_binding_constraint(
            study, binding_constraint_id
        )

    @bp.put(
        "/studies/{uuid}/bindingconstraints/{binding_constraint_id}",
        tags=[APITag.study_data],
        summary="Update binding constraint",
        response_model=None,  # Dict[str, bool],
    )
    def update_binding_constraint(
        uuid: str,
        binding_constraint_id: str,
        data: UpdateBindingConstProps,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Update binding constraint {binding_constraint_id} for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(
            uuid, StudyPermissionType.READ, params
        )
        return (
            study_service.binding_constraint_manager.update_binding_constraint(
                study, binding_constraint_id, data
            )
        )

    @bp.post(
        "/studies/{uuid}/bindingconstraints/{binding_constraint_id}/term",
        tags=[APITag.study_data],
        summary="update constraint term",
    )
    def add_constraint_term(
        uuid: str,
        binding_constraint_id: str,
        data: ConstraintTermDTO,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"add constraint term from {binding_constraint_id} for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(
            uuid, StudyPermissionType.WRITE, params
        )
        return (
            study_service.binding_constraint_manager.add_new_constraint_term(
                study, binding_constraint_id, data
            )
        )

    @bp.put(
        "/studies/{uuid}/bindingconstraints/{binding_constraint_id}/term",
        tags=[APITag.study_data],
        summary="update constraint term",
    )
    def update_constraint_term(
        uuid: str,
        binding_constraint_id: str,
        data: ConstraintTermDTO,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"update constraint term from {binding_constraint_id} for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(
            uuid, StudyPermissionType.WRITE, params
        )
        return study_service.binding_constraint_manager.update_constraint_term(
            study, binding_constraint_id, data
        )

    @bp.delete(
        "/studies/{uuid}/bindingconstraints/{binding_constraint_id}/term/{term_id}",
        tags=[APITag.study_data],
        summary="update constraint term",
    )
    def remove_constraint_term(
        uuid: str,
        binding_constraint_id: str,
        term_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"delete constraint term {term_id} from {binding_constraint_id} for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(
            uuid, StudyPermissionType.WRITE, params
        )
        return study_service.binding_constraint_manager.remove_constraint_term(
            study, binding_constraint_id, term_id
        )

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
        study = study_service.check_study_access(
            uuid, StudyPermissionType.READ, params
        )

        return study_service.advanced_parameters_manager.get_field_values(
            study
        )

    @bp.put(
        path="/studies/{uuid}/config/advancedparameters/form",
        tags=[APITag.study_data],
        summary="Set Advanced parameters new values",
    )
    def set_advanced_params(
        uuid: str,
        field_values: AdvancedParamsFormFields,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> None:
        logger.info(
            f"Updating Advanced parameters values for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(
            uuid, StudyPermissionType.WRITE, params
        )

        study_service.advanced_parameters_manager.set_field_values(
            study, field_values
        )

    @bp.put(
        "/studies/{uuid}/timeseries/generate",
        tags=[APITag.study_data],
        summary="Generate timeseries",
    )
    def generate_timeseries(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Generating timeseries for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(
            uuid, StudyPermissionType.WRITE, params
        )

        return study_service.generate_timeseries(study, params)

    return bp
