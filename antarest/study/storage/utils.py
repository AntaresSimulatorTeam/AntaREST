import logging
import os
import shutil
from pathlib import Path
from uuid import uuid4

from antarest.core.config import Config
from antarest.core.exceptions import StudyValidationError
from antarest.study.model import (
    DEFAULT_WORKSPACE_NAME,
    Study,
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
