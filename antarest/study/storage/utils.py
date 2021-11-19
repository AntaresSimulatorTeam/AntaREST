import logging
import os
import shutil
from pathlib import Path
from typing import Optional, Union
from uuid import uuid4
from zipfile import ZipFile

from antarest.core.config import Config
from antarest.core.exceptions import (
    StudyValidationError,
    UnsupportedStudyVersion,
)
from antarest.core.interfaces.cache import CacheConstants, ICache
from antarest.core.jwt import JWTUser
from antarest.core.model import PermissionInfo, StudyPermissionType, PublicMode
from antarest.core.permissions import check_permission
from antarest.core.requests import UserHasNotPermissionError
from antarest.study.model import (
    DEFAULT_WORKSPACE_NAME,
    Study,
    STUDY_REFERENCE_TEMPLATES,
    StudyMetadataDTO,
)
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import (
    FileStudyTree,
)

logger = logging.getLogger(__name__)


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


def fix_study_root(study_path: Path) -> None:
    """
    Fix possibly the wrong study root on zipped archive (when the study root is nested)

    @param study_path the study initial root path
    """
    if not study_path.is_dir():
        raise StudyValidationError("Not a directory")

    root_path = study_path
    contents = os.listdir(root_path)
    sub_root_path = None
    while len(contents) == 1 and (root_path / contents[0]).is_dir():
        new_root = root_path / contents[0]
        if sub_root_path is None:
            sub_root_path = root_path / str(uuid4())
            shutil.move(str(new_root), str(sub_root_path))
            new_root = sub_root_path

        logger.debug(f"Searching study root in {new_root}")
        root_path = new_root
        if not new_root.is_dir():
            raise StudyValidationError("Not a directory")
        contents = os.listdir(new_root)

    if sub_root_path is not None:
        for item in os.listdir(root_path):
            shutil.move(str(root_path / item), str(study_path))
        shutil.rmtree(sub_root_path)


def is_managed(study: Study) -> bool:
    return (
        not hasattr(study, "workspace")
        or study.workspace == DEFAULT_WORKSPACE_NAME
    )


def remove_from_cache(cache: ICache, root_id: str) -> None:
    cache.invalidate_all(
        [
            f"{CacheConstants.RAW_STUDY}/{root_id}",
            f"{CacheConstants.STUDY_FACTORY}/{root_id}",
        ]
    )


def create_new_empty_study(
    version: str, path_study: Path, path_resources: Path
) -> None:
    version_template: Optional[str] = STUDY_REFERENCE_TEMPLATES.get(
        version, None
    )
    if version_template is None:
        raise UnsupportedStudyVersion(version)

    empty_study_zip = path_resources / version_template

    with ZipFile(empty_study_zip) as zip_output:
        zip_output.extractall(path=path_study)


def create_permission_from_study(
    study: Union[Study, StudyMetadataDTO]
) -> PermissionInfo:
    return PermissionInfo(
        owner=study.owner.id if study.owner is not None else None,
        groups=[g.id for g in study.groups if g.id is not None],
        public_mode=PublicMode(study.public_mode)
        if study.public_mode is not None
        else PublicMode.NONE,
    )


def assert_permission(
    user: Optional[JWTUser],
    study: Optional[Union[Study, StudyMetadataDTO]],
    permission_type: StudyPermissionType,
    raising: bool = True,
) -> bool:
    """
    Assert user has permission to edit or read study.
    Args:
        user: user logged
        study: study asked
        permission_type: level of permission
        raising: raise error if permission not matched

    Returns: true if permission match, false if not raising.

    """
    if not user:
        logger.error("FAIL permission: user is not logged")
        raise UserHasNotPermissionError()

    if not study:
        logger.error("FAIL permission: study not exist")
        raise ValueError("Metadata is None")

    permission_info = create_permission_from_study(study)
    ok = check_permission(user, permission_info, permission_type)
    if raising and not ok:
        logger.error(
            "FAIL permission: user %d has no permission on study %s",
            user.id,
            study.id,
        )
        raise UserHasNotPermissionError()

    return ok
