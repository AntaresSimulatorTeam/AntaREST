import logging
from typing import List, Optional

from antarest.core.config import Config
from antarest.core.exceptions import CannotScanInternalWorkspace
from antarest.study.model import DEFAULT_WORKSPACE_NAME, NonStudyFolder
from antarest.study.storage.utils import (
    get_folder_from_workspace,
    get_workspace_from_config,
    is_folder_safe,
    is_study_folder,
)

logger = logging.getLogger(__name__)


class Explorer:
    def __init__(self, config: Config):
        self.config = config

    def list_dir(
        self,
        workspace_name: str,
        workspace_directory_path: str,
    ) -> List[NonStudyFolder]:
        """
        return a list of all directories under workspace_directory_path, that aren't studies.
        """
        workspace = get_workspace_from_config(self.config, workspace_name)
        directory_path = get_folder_from_workspace(workspace, workspace_directory_path)
        directories = []
        for child in directory_path.iterdir():
            if child.is_dir() and not is_study_folder(child):
                directories.append(NonStudyFolder(path=str(child), workspace=workspace_name, name=child.name))
        return directories

    def list_workspaces(
        self,
    ) -> List[str]:
        """
        Return the list of all configured workspace name, except the default one.
        """
        return [
            workspace_name
            for workspace_name in self.config.storage.workspaces.keys()
            if workspace_name != DEFAULT_WORKSPACE_NAME
        ]
