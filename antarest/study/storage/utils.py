from logging import Logger
from pathlib import Path
from typing import Optional, cast, List, Union

from antarest.core.config import Config
from antarest.core.custom_types import JSON
from antarest.core.exceptions import StudyTypeUnsupported
from antarest.core.interfaces.cache import ICache, CacheConstants
from antarest.login.model import GroupDTO
from antarest.study.common.studystorage import IStudyStorageService
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
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy
from antarest.study.storage.variantstudy.variant_study_service import (
    VariantStudyService,
)


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


# def get_study_path(metadata: Study) -> Path:
#     """
#     Get study path
#     Args:
#         metadata: study information
#
#     Returns: study path
#
#     """
#     if hasattr(metadata, "path"):
#         return Path(metadata.path)
#     raise StudyTypeUnsupported(metadata.id, metadata.type)


def remove_from_cache(cache: ICache, root_id: str) -> None:
    cache.invalidate_all(
        [
            f"{root_id}/{CacheConstants.RAW_STUDY}",
            f"{root_id}/{CacheConstants.STUDY_FACTORY}",
        ]
    )


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
        version=int(study.version),
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


def get_using_cache(
    study_service: Union[VariantStudyService, RawStudyService],
    metadata: Study,
    logger: Logger,
    url: str = "",
    depth: int = 3,
    formatted: bool = True,
) -> JSON:
    """
    Entry point to fetch data inside study.
    Args:
        study_service: study service
        metadata: study
        logger: Logger
        url: path data inside study to reach
        depth: tree depth to reach after reach data path
        formatted: indicate if raw files must be parsed and formatted

    Returns: study data formatted in json

    """
    study_path = study_service.get_study_path(metadata)

    _, study = study_service.study_factory.create_from_fs(
        study_path, metadata.id
    )
    parts = [item for item in url.split("/") if item]

    data: JSON = dict()
    if url == "" and depth == -1:
        cache_id = f"{metadata.id}/{CacheConstants.RAW_STUDY}"
        from_cache = study_service.cache.get(cache_id)
        if from_cache is not None:
            logger.info(f"Raw Study {metadata.id} read from cache")
            data = from_cache
        else:
            data = study.get(parts, depth=depth, formatted=formatted)
            study_service.cache.put(cache_id, data)
            logger.info(
                f"Cache new entry from RawStudyService (studyID: {metadata.id})"
            )
    else:
        data = study.get(parts, depth=depth, formatted=formatted)
    del study
    return data
