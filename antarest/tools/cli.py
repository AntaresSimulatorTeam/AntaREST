import logging
from pathlib import Path
from typing import Optional

import click

from antarest.tools.lib import CLIVariantManager

logging.basicConfig(level=logging.INFO)


@click.group()
def commands() -> None:
    pass


@commands.command()
@click.option(
    "--host",
    "-h",
    nargs=1,
    required=True,
    type=str,
    help="Host URL of the antares web instance",
)
@click.option(
    "--auth_token",
    nargs=1,
    required=False,
    default=None,
    type=str,
    help="Authentication token if server needs one",
)
@click.option(
    "--input",
    "-i",
    nargs=1,
    required=True,
    type=click.Path(exists=True),
    help="Variant script source path",
)
@click.option(
    "--study_id",
    "-s",
    nargs=1,
    required=True,
    type=str,
    help="ID of the variant to apply the script onto",
)
def apply_script(
    host: str, input: str, study_id: str, token: Optional[str] = None
) -> None:
    """Apply a variant script onto an AntaresWeb study variant"""
    vm = CLIVariantManager(host, token)
    res = vm.apply_commands_from_dir(study_id, Path(input))
    print(res)


@commands.command()
@click.option(
    "--input",
    "-i",
    nargs=1,
    required=True,
    type=click.Path(exists=True),
    help="Study fragment path",
)
@click.option(
    "--output",
    "-o",
    nargs=1,
    required=True,
    type=click.Path(exists=False),
    help="Script output path",
)
def generate_script(input: str, output: str) -> None:
    """Generate variant script commands from a study or study fragment"""
    CLIVariantManager.extract_commands(Path(input), Path(output))


if __name__ == "__main__":
    commands()
