import logging
from pathlib import Path

from antarest.core.config import Config
from antarest.core.utils.utils import get_local_path
from antarest.launcher.adapters.slurm_launcher.slurm_launcher import (
    WORKSPACE_LOCK_FILE_NAME,
)

logger = logging.getLogger(__name__)


def clean_locks(config: Path) -> None:
    """Clean app locks"""
    res = get_local_path() / "resources"
    config_obj = Config.from_yaml_file(res=res, file=config)
    if config_obj.launcher.slurm:
        slurm_workspace = config_obj.launcher.slurm.local_workspace
        if slurm_workspace.exists() and slurm_workspace.is_dir():
            for workspace in slurm_workspace.iterdir():
                lock_file = workspace / WORKSPACE_LOCK_FILE_NAME
                if lock_file.exists():
                    logger.info(
                        f"Removing slurm workspace lock file {lock_file}"
                    )
                    lock_file.unlink()
