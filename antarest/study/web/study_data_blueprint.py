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
from antarest.study.business.area_management import (
    AreaType,
    AreaCreationDTO,
    AreaInfoDTO,
    AreaUI,
)
from antarest.study.business.config_management import (
    OutputVariable,
)
from antarest.study.business.link_management import LinkInfoDTO
from antarest.study.business.optimization_management import (
    OptimizationFormFields,
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

    return bp
