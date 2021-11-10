import io
import logging
from http import HTTPStatus
from pathlib import Path
from typing import Any, Optional, List, Dict

from fastapi import APIRouter, File, Depends, Request, HTTPException, Body
from markupsafe import escape
from starlette.responses import FileResponse

from antarest.core.config import Config
from antarest.core.jwt import JWTUser
from antarest.core.requests import (
    RequestParameters,
)
from antarest.core.utils.file_transfer import FileTransferManager
from antarest.core.utils.utils import sanitize_uuid
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth
from antarest.study.model import (
    PublicMode,
    StudyMetadataPatchDTO,
    StudySimResultDTO,
    StudyMetadataDTO,
    MatrixAggregationResult,
    CommentsDto,
    StudyDownloadDTO,
)
from antarest.study.service import StudyService
from antarest.study.storage.study_download_utils import StudyDownloader

logger = logging.getLogger(__name__)


def create_study_routes(
    study_service: StudyService, config: Config
) -> APIRouter:
    """
    Endpoint implementation for studies management
    Args:
        study_service: study service facade to handle request
        config: main server configuration

    Returns:

    """
    bp = APIRouter(prefix="/v1")
    auth = Auth(config)
    ftm = FileTransferManager.get_instance(config)

    @bp.get(
        "/studies",
        tags=[APITag.study_management],
        summary="Get Studies",
        response_model=Dict[str, StudyMetadataDTO],
    )
    def get_studies(
        summary: bool = False,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(f"Fetching study list", extra={"user": current_user.id})
        params = RequestParameters(user=current_user)
        available_studies = study_service.get_studies_information(
            summary, params
        )
        return available_studies

    @bp.get(
        "/studies/{uuid}/comments",
        tags=[APITag.study_management],
        summary="Get comments",
    )
    def get_comments(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Get comments of study {uuid}", extra={"user": current_user.id}
        )
        params = RequestParameters(user=current_user)
        study_id = sanitize_uuid(uuid)
        return study_service.get_comments(study_id, params)

    @bp.put(
        "/studies/{uuid}/comments",
        status_code=HTTPStatus.NO_CONTENT.value,
        tags=[APITag.study_raw_data],
        summary="Update comments",
    )
    def edit_comments(
        uuid: str,
        data: CommentsDto,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Editing comments for study {uuid}",
            extra={"user": current_user.id},
        )
        new = data
        if not new:
            raise HTTPException(
                status_code=400, detail="empty body not authorized"
            )
        study_id = sanitize_uuid(uuid)
        params = RequestParameters(user=current_user)
        study_service.edit_comments(study_id, new, params)

    @bp.post(
        "/studies/_import",
        status_code=HTTPStatus.CREATED,
        tags=[APITag.study_management],
        summary="Import Study",
        response_model=str,
    )
    def import_study(
        study: bytes = File(...),
        groups: Optional[str] = None,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(f"Importing new study", extra={"user": current_user.id})
        zip_binary = io.BytesIO(study)

        params = RequestParameters(user=current_user)
        group_ids = groups.split(",") if groups is not None else []

        uuid = study_service.import_study(zip_binary, group_ids, params)

        return uuid

    @bp.post(
        "/studies/{uuid}/copy",
        status_code=HTTPStatus.CREATED,
        tags=[APITag.study_management],
        summary="Copy Study",
        response_model=str,
    )
    def copy_study(
        uuid: str,
        dest: str,
        with_outputs: bool = False,
        groups: Optional[str] = None,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Copying study {uuid} into new study '{dest}'",
            extra={"user": current_user.id},
        )
        source_uuid = uuid
        group_ids = groups.split(",") if groups is not None else []
        source_uuid_sanitized = sanitize_uuid(source_uuid)
        destination_name_sanitized = escape(dest)

        params = RequestParameters(user=current_user)

        destination_uuid = study_service.copy_study(
            src_uuid=source_uuid_sanitized,
            dest_study_name=destination_name_sanitized,
            group_ids=group_ids,
            with_outputs=with_outputs,
            params=params,
        )

        return destination_uuid

    @bp.post(
        "/studies",
        status_code=HTTPStatus.CREATED,
        tags=[APITag.study_management],
        summary="Create a new empty study",
        response_model=str,
    )
    def create_study(
        name: str,
        version: Optional[str] = None,
        groups: Optional[str] = None,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Creating new study '{name}'", extra={"user": current_user.id}
        )
        name_sanitized = escape(name)
        group_ids = groups.split(",") if groups is not None else []
        group_ids = [sanitize_uuid(gid) for gid in group_ids]

        params = RequestParameters(user=current_user)
        uuid = study_service.create_study(
            name_sanitized, version, group_ids, params
        )

        return uuid

    @bp.get(
        "/studies/{uuid}/export",
        tags=[APITag.study_management],
        summary="Export Study",
        response_class=FileResponse,
        responses={
            200: {
                "content": {
                    "application/zip": {},
                },
            },
        },
    )
    def export_study(
        uuid: str,
        no_output: Optional[bool] = False,
        request_tmp_file: Path = Depends(ftm.request_tmp_file),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(f"Exporting study {uuid}", extra={"user": current_user.id})
        uuid_sanitized = sanitize_uuid(uuid)

        params = RequestParameters(user=current_user)
        export_path = study_service.export_study(
            uuid_sanitized, request_tmp_file, params, not no_output
        )

        return FileResponse(
            export_path,
            headers={
                "Content-Disposition": f'attachment; filename="{uuid_sanitized}.zip'
            },
            media_type="application/zip",
        )

    @bp.delete(
        "/studies/{uuid}",
        status_code=HTTPStatus.OK,
        tags=[APITag.study_management],
        summary="Delete Study",
    )
    def delete_study(
        uuid: str, current_user: JWTUser = Depends(auth.get_current_user)
    ) -> Any:
        logger.info(f"Deleting study {uuid}", extra={"user": current_user.id})
        uuid_sanitized = sanitize_uuid(uuid)

        params = RequestParameters(user=current_user)
        study_service.delete_study(uuid_sanitized, params)

        return ""

    @bp.post(
        "/studies/{uuid}/output",
        status_code=HTTPStatus.ACCEPTED,
        tags=[APITag.study_outputs],
        summary="Import Output",
        response_model=str,
    )
    def import_output(
        uuid: str,
        output: bytes = File(...),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Importing output for study {uuid}",
            extra={"user": current_user.id},
        )
        uuid_sanitized = sanitize_uuid(uuid)

        zip_binary = io.BytesIO(output)

        params = RequestParameters(user=current_user)
        output_id = study_service.import_output(
            uuid_sanitized, zip_binary, params
        )
        return output_id

    @bp.put(
        "/studies/{uuid}/owner/{user_id}",
        tags=[APITag.study_permissions],
        summary="Change study owner",
    )
    def change_owner(
        uuid: str,
        user_id: int,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Changing owner to {user_id} for study {uuid}",
            extra={"user": current_user.id},
        )
        uuid_sanitized = sanitize_uuid(uuid)
        params = RequestParameters(user=current_user)
        study_service.change_owner(uuid_sanitized, user_id, params)

        return ""

    @bp.put(
        "/studies/{uuid}/groups/{group_id}",
        tags=[APITag.study_permissions],
        summary="Add a group association",
    )
    def add_group(
        uuid: str,
        group_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Adding group {group_id} to study {uuid}",
            extra={"user": current_user.id},
        )
        uuid_sanitized = sanitize_uuid(uuid)
        group_id = sanitize_uuid(group_id)
        params = RequestParameters(user=current_user)
        study_service.add_group(uuid_sanitized, group_id, params)

        return ""

    @bp.delete(
        "/studies/{uuid}/groups/{group_id}",
        tags=[APITag.study_permissions],
        summary="Remove a group association",
    )
    def remove_group(
        uuid: str,
        group_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Removing group {group_id} to study {uuid}",
            extra={"user": current_user.id},
        )
        uuid_sanitized = sanitize_uuid(uuid)
        group_id = sanitize_uuid(group_id)

        params = RequestParameters(user=current_user)
        study_service.remove_group(uuid_sanitized, group_id, params)

        return ""

    @bp.put(
        "/studies/{uuid}/public_mode/{mode}",
        tags=[APITag.study_permissions],
        summary="Set study public mode",
    )
    def set_public_mode(
        uuid: str,
        mode: PublicMode,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Setting public mode to {mode} for study {uuid}",
            extra={"user": current_user.id},
        )
        uuid_sanitized = sanitize_uuid(uuid)
        params = RequestParameters(user=current_user)
        study_service.set_public_mode(uuid_sanitized, mode, params)

        return ""

    @bp.get(
        "/studies/_versions",
        tags=[APITag.study_management],
        summary="Show available study versions",
    )
    def get_studies_version(
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        params = RequestParameters(user=current_user)
        logger.info(f"Fetching version list")
        return StudyService.get_studies_versions(params=params)

    @bp.get(
        "/studies/{uuid}",
        tags=[APITag.study_management],
        summary="Get Study information",
        response_model=StudyMetadataDTO,
    )
    def get_study_metadata(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Fetching study {uuid} metadata", extra={"user": current_user.id}
        )
        params = RequestParameters(user=current_user)
        study_metadata = study_service.get_study_information(uuid, params)
        return study_metadata

    @bp.put(
        "/studies/{uuid}",
        tags=[APITag.study_management],
        summary="Update Study information",
        response_model=StudyMetadataDTO,
    )
    def update_study_metadata(
        uuid: str,
        study_metadata_patch: StudyMetadataPatchDTO,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Updating metadata for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study_metadata = study_service.update_study_information(
            uuid, study_metadata_patch, params
        )
        return study_metadata

    @bp.post(
        "/studies/{study_id}/outputs/{output_id}/download",
        tags=[APITag.study_outputs],
        summary="Get outputs data",
        responses={
            200: {
                "content": {
                    "application/json": {},
                    "application/zip": {},
                    "application/tar+gz": {},
                },
            },
        },
        response_model=MatrixAggregationResult,
    )
    def output_download(
        study_id: str,
        output_id: str,
        request: Request,
        data: Optional[StudyDownloadDTO] = Body(default=None),
        tmp_export_file: Path = Depends(ftm.request_tmp_file),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        study_id = sanitize_uuid(study_id)
        output_id = sanitize_uuid(output_id)
        if not data:
            logger.info(
                f"Fetching whole output of the simulation {output_id} for study {study_id}"
            )
            params = RequestParameters(user=current_user)
            export_path = study_service.export_output(
                study_uuid=study_id,
                output_uuid=output_id,
                target=tmp_export_file,
                params=params,
            )

            return FileResponse(
                export_path,
                headers={
                    "Content-Disposition": f'attachment; filename="{output_id}.zip'
                },
                media_type="application/zip",
            )
        else:
            logger.info(
                f"Fetching batch outputs of simulation {output_id} for study {study_id}",
                extra={"user": current_user.id},
            )
            params = RequestParameters(user=current_user)
            content = study_service.download_outputs(
                study_id, output_id, data, params
            )
            accept = request.headers.get("Accept")
            if accept == "application/zip" or accept == "application/tar+gz":
                StudyDownloader.export(content, accept, tmp_export_file)
                return FileResponse(
                    tmp_export_file,
                    headers={
                        "Content-Disposition": f'attachment; filename="output-{output_id}.zip'
                    },
                    media_type=accept,
                )
            return content

    @bp.get(
        "/studies/{study_id}/outputs",
        summary="Get global information about a study simulation result",
        tags=[APITag.study_outputs],
        response_model=List[StudySimResultDTO],
    )
    def sim_result(
        study_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Fetching output list for study {study_id}",
            extra={"user": current_user.id},
        )
        study_id = sanitize_uuid(study_id)
        params = RequestParameters(user=current_user)
        content = study_service.get_study_sim_result(study_id, params)
        return content

    @bp.put(
        "/studies/{study_id}/outputs/{output_id}/reference",
        summary="Set simulation as the reference output",
        tags=[APITag.study_outputs],
    )
    def set_sim_reference(
        study_id: str,
        output_id: str,
        status: bool = True,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Setting output {output_id} as reference simulation for study {study_id}",
            extra={"user": current_user.id},
        )
        study_id = sanitize_uuid(study_id)
        output_id = sanitize_uuid(output_id)
        params = RequestParameters(user=current_user)
        study_service.set_sim_reference(study_id, output_id, status, params)
        return ""

    @bp.put(
        "/studies/{study_id}/archive",
        summary="Archive a study",
        tags=[APITag.study_management],
    )
    def archive_study(
        study_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Archiving study {study_id}", extra={"user": current_user.id}
        )
        study_id = sanitize_uuid(study_id)
        params = RequestParameters(user=current_user)
        study_service.archive(study_id, params)
        return ""

    @bp.put(
        "/studies/{study_id}/unarchive",
        summary="Dearchive a study",
        tags=[APITag.study_management],
    )
    def unarchive_study(
        study_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Unarchiving study {study_id}", extra={"user": current_user.id}
        )
        study_id = sanitize_uuid(study_id)
        params = RequestParameters(user=current_user)
        study_service.unarchive(study_id, params)
        return ""

    return bp
