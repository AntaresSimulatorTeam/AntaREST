from alembic.config import Config
from alembic import command

alembic_cfg = Config("alembic.ini")


def get_current():
    command.current(alembic_cfg)
    command.upgrade(alembic_cfg, "head")
