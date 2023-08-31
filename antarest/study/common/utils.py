import logging
from typing import Optional

from antarest.core.model import PublicMode
from antarest.login.model import GroupDTO
from antarest.study.model import (
    DEFAULT_WORKSPACE_NAME,
    OwnerInfo,
    Patch,
    PatchStudy,
    Study,
    StudyAdditionalData,
    StudyMetadataDTO,
)

logger = logging.getLogger(__name__)


def get_study_information(study: Study) -> StudyMetadataDTO:
    additional_data = study.additional_data or StudyAdditionalData()

    try:
        patch = Patch.parse_raw(additional_data.patch or "{}")
    except Exception as e:
        logger.warning(
            f"Failed to parse patch for study {study.id}", exc_info=e
        )
        patch = Patch()

    patch_metadata = patch.study or PatchStudy()

    study_workspace = getattr(study, "workspace", DEFAULT_WORKSPACE_NAME)
    folder: Optional[str] = None
    if hasattr(study, "folder"):
        folder = study.folder

    owner_info = (
        OwnerInfo(id=study.owner.id, name=study.owner.name)
        if study.owner is not None
        else OwnerInfo(name=additional_data.author or "Unknown")
    )

    return StudyMetadataDTO(
        id=study.id,
        name=study.name,
        version=int(study.version),
        created=str(study.created_at),
        updated=str(study.updated_at),
        workspace=study_workspace,
        managed=study_workspace == DEFAULT_WORKSPACE_NAME,
        type=study.type,
        archived=study.archived if study.archived is not None else False,
        owner=owner_info,
        groups=[
            GroupDTO(id=group.id, name=group.name) for group in study.groups
        ],
        public_mode=study.public_mode or PublicMode.NONE,
        horizon=additional_data.horizon,
        scenario=patch_metadata.scenario,
        status=patch_metadata.status,
        doc=patch_metadata.doc,
        folder=folder,
        tags=patch_metadata.tags,
    )
