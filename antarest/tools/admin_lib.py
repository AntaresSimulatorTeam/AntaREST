import logging
from pathlib import Path

from antarest.core.config import Config
from antarest.core.utils.utils import get_local_path
from antarest.launcher.adapters.slurm_launcher.slurm_launcher import (
    WORKSPACE_LOCK_FILE_NAME,
)

logger = logging.getLogger(__name__)


def get_config(config_path: Path) -> Config:
    res = get_local_path() / "resources"
    config_obj = Config.from_yaml_file(res=res, file=config_path)
    return config_obj


def clean_locks_from_config(config: Config) -> None:
    if config.launcher.slurm:
        slurm_workspace = config.launcher.slurm.local_workspace
        if slurm_workspace.exists() and slurm_workspace.is_dir():
            for workspace in slurm_workspace.iterdir():
                lock_file = workspace / WORKSPACE_LOCK_FILE_NAME
                if lock_file.exists():
                    logger.info(
                        f"Removing slurm workspace lock file {lock_file}"
                    )
                    lock_file.unlink()


def clean_locks(config: Path) -> None:
    """Clean app locks"""
    config_obj = get_config(config)
    clean_locks_from_config(config_obj)


def reindex_table(config: Path) -> None:
    import sqlalchemy  # type: ignore
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

    config_obj = get_config(config)
    engine = sqlalchemy.create_engine(config_obj.db.db_admin_url, echo=True)
    connection = engine.raw_connection()
    connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = connection.cursor()
    cursor.execute("VACUUM ANALYSE study")
    cursor.execute("REINDEX INDEX study_pkey")
    cursor.execute("VACUUM ANALYSE rawstudy")
    cursor.execute("REINDEX INDEX rawstudy_pkey")
