import logging
from typing import Any, Optional, List, Dict, Union

from fastapi import APIRouter, Depends, Body

from antarest.core.config import Config
from antarest.core.jwt import JWTUser
from antarest.core.model import StudyPermissionType
from antarest.core.requests import (
    RequestParameters,
)
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth
from antarest.matrixstore.business.matrix_editor import (
    MatrixEditInstructionDTO,
)
from antarest.study.business.advanced_parameters_management import (
    AdvancedParamsFormFields,
)
from antarest.study.business.area_management import (
    AreaType,
    AreaCreationDTO,
    AreaInfoDTO,
    AreaUI,
)
from antarest.study.business.binding_constraint_management import (
    ConstraintTermDTO,
    UpdateBindingConstProps,
)
from antarest.study.business.config_management import (
    OutputVariable,
)
from antarest.study.business.hydro_management import (
    ManagementOptionsFormFields,
)
from antarest.study.business.link_management import (
    LinkInfoDTO,
)
from antarest.study.business.optimization_management import (
    OptimizationFormFields,
)
from antarest.study.business.table_mode_management import (
    TableTemplateType,
    ColumnModelTypes,
)
from antarest.study.business.timeseries_config_management import (
    TSFormFields,
)
from antarest.study.model import PatchCluster, PatchArea
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
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Updating area ui {area_id} for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        return study_service.update_area_ui(uuid, area_id, area_ui, params)

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
        "/studies/{uuid}/areas/{area_id}/hydro/config",
        tags=[APITag.study_data],
        summary="Get management options form fields for a given area",
        response_model=ManagementOptionsFormFields,
        response_model_exclude_none=True,
    )
    def get_management_options(
        uuid: str,
        area_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> ManagementOptionsFormFields:
        logger.info(
            msg=f"Getting management options for area {area_id}  of study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(
            uuid, StudyPermissionType.READ, params
        )

        return study_service.hydro_manager.get_field_values(study, area_id)

    @bp.put(
        "/studies/{uuid}/areas/{area_id}/hydro/config",
        tags=[APITag.study_data],
        summary="Set management options form fields for a given area",
    )
    def set_management_options(
        uuid: str,
        area_id: str,
        data: ManagementOptionsFormFields,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            msg=f"Setting management options for area {area_id}  of study {uuid}",
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
        "/studies/{uuid}/config/thematic_trimming",
        tags=[APITag.study_data],
        summary="Get thematic trimming config",
        response_model=Dict[str, bool],
    )
    def get_thematic_trimming(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Fetching thematic trimming config for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(
            uuid, StudyPermissionType.READ, params
        )
        return study_service.config_manager.get_thematic_trimming(study)

    @bp.put(
        path="/studies/{uuid}/config/thematic_trimming",
        tags=[APITag.study_data],
        summary="Set thematic trimming config",
    )
    def set_thematic_trimming(
        uuid: str,
        thematic_trimming_config: Dict[OutputVariable, bool] = Body(...),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Updating thematic trimming config for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study = study_service.check_study_access(
            uuid, StudyPermissionType.WRITE, params
        )
        study_service.config_manager.set_thematic_trimming(
            study,
            {
                output_variable.value: thematic_trimming_config[
                    output_variable
                ]
                for output_variable in thematic_trimming_config
            },
        )

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
            f"Updating playlist confi for study {uuid}",
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
        path="/studies/{uuid}/config/optimization_form_fields",
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
        path="/studies/{uuid}/config/optimization_form_fields",
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
        path="/studies/{uuid}/config/timeseries_form_fields",
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
        path="/studies/{uuid}/config/timeseries_form_fields",
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
        path="/studies/{uuid}/table_mode",
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
        path="/studies/{uuid}/table_mode",
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
        path="/studies/{uuid}/config/advanced_parameters",
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
        path="/studies/{uuid}/config/advanced_parameters",
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

    return bp
