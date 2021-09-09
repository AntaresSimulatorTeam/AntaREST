from logging import Logger
from pathlib import Path
from typing import Optional, cast

from antarest.core.config import Config
from antarest.core.exceptions import StudyTypeUnsupported
from antarest.login.model import GroupDTO
from antarest.study.model import (
    DEFAULT_WORKSPACE_NAME,
    Study,
    StudyMetadataDTO,
    PatchStudy,
    OwnerInfo,
    PublicMode,
    RawStudy,
)
from antarest.study.storage.patch_service import PatchService
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import (
    StudyFactory,
)
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import (
    FileStudyTree,
)
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy


def get_workspace_path(config: Config, workspace: str) -> Path:
    """
    Retrieve workspace path from config

    Args:
        workspace: workspace name
        config: antarest config
    Returns: path

    """
    return config.storage.workspaces[workspace].path


def get_default_workspace_path(config: Config) -> Path:
    """
    Get path of default workspace
    Returns: path

    """
    return get_workspace_path(config, DEFAULT_WORKSPACE_NAME)


def update_antares_info(metadata: Study, studytree: FileStudyTree) -> None:
    """
    Update study.antares data
    Args:
        metadata: study information
        studytree: study tree

    Returns: none, update is directly apply on study_data

    """
    study_data_info = studytree.get(["study"])
    study_data_info["antares"]["caption"] = metadata.name
    study_data_info["antares"]["created"] = metadata.created_at.timestamp()
    study_data_info["antares"]["lastsave"] = metadata.updated_at.timestamp()
    study_data_info["antares"]["version"] = metadata.version
    studytree.save(study_data_info, ["study"])


def get_study_path(metadata: Study) -> Path:
    """
    Get study path
    Args:
        metadata: study information

    Returns: study path

    """
    if hasattr(metadata, "path"):
        return Path(metadata.path)
    raise StudyTypeUnsupported(metadata.id, metadata.type)


def get_study_information(
    study: Study,
    study_path: Optional[Path],
    patch_service: PatchService,
    study_factory: StudyFactory,
    logger: Logger,
    summary: bool,
) -> StudyMetadataDTO:
    file_settings = {}
    file_metadata = {}

    patch_metadata = patch_service.get(study).study or PatchStudy()

    try:
        if study_path:
            config = FileStudyTreeConfig(
                study_path=study_path,
                path=study_path,
                study_id="",
                version=-1,
            )
            raw_study = study_factory.create_from_config(config)
            file_metadata = raw_study.get(url=["study", "antares"])
            file_settings = raw_study.get(
                url=["settings", "generaldata", "general"]
            )
    except Exception as e:
        logger.error(
            "Failed to retrieve general settings for study %s",
            study.id,
            exc_info=e,
        )

    study_workspace = DEFAULT_WORKSPACE_NAME
    if hasattr(study, "workspace"):
        study_workspace = study.workspace

    return StudyMetadataDTO(
        id=study.id,
        name=study.name,
        version=study.version,
        created=study.created_at.timestamp(),
        updated=study.updated_at.timestamp(),
        workspace=study_workspace,
        managed=study_workspace == DEFAULT_WORKSPACE_NAME,
        type=study.type,
        archived=study.archived if study.archived is not None else False,
        owner=OwnerInfo(id=study.owner.id, name=study.owner.name)
        if study.owner is not None
        else OwnerInfo(name=file_metadata.get("author", "Unknown")),
        groups=[
            GroupDTO(id=group.id, name=group.name) for group in study.groups
        ],
        public_mode=study.public_mode or PublicMode.NONE,
        horizon=file_settings.get("horizon", None),
        scenario=patch_metadata.scenario,
        status=patch_metadata.status,
        doc=patch_metadata.doc,
    )
