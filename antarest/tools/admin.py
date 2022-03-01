import logging
from pathlib import Path

import click

from antarest.tools.admin_lib import clean_locks as do_clean_locks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.group()
def commands() -> None:
    pass


@commands.command()
@click.option(
    "--config",
    "-c",
    nargs=1,
    required=True,
    type=click.Path(exists=True),
    help="Application config",
)
def clean_locks(config: str) -> None:
    """Clean app locks"""
    do_clean_locks(Path(config))


if __name__ == "__main__":
    commands()
