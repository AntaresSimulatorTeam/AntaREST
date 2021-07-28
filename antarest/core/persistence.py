import logging
import os
from io import StringIO
from pathlib import Path

from alembic import command  # type: ignore
from alembic.config import Config  # type: ignore
from alembic.util import CommandError  # type: ignore
from sqlalchemy.ext.declarative import declarative_base  # type: ignore

logger = logging.getLogger(__name__)

Base = declarative_base()


def upgrade_db(config_file: Path) -> None:
    os.environ.setdefault("ANTAREST_CONF", str(config_file))
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.stdout = StringIO()
    try:
        command.current(alembic_cfg)
        current_version_output = alembic_cfg.stdout.getvalue()
        current_version = current_version_output.strip()
    except CommandError as e:
        logger.error(
            "Failed to find current database version, make sure you use the latest version of the application",
            exc_info=e,
        )
        raise e

    alembic_cfg.stdout = StringIO()
    command.heads(alembic_cfg)
    head_output = alembic_cfg.stdout.getvalue()
    head = head_output.split(" ")[0].strip()
    if current_version != head:
        logger.info(f"Upgrading database from {current_version} to {head}")
        command.upgrade(alembic_cfg, head)
    logger.info(f"Database up to date")
