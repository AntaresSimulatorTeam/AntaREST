from pathlib import Path

from antarest.core.config import Config
from antarest.study.model import DEFAULT_WORKSPACE_NAME


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
