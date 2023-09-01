import logging
from pathlib import Path
from typing import Optional

import click

from antarest.study.model import NEW_DEFAULT_STUDY_VERSION
from antarest.study.storage.study_upgrader import upgrade_study
from antarest.tools.lib import extract_commands, generate_diff, generate_study


@click.group(context_settings={"max_content_width": 120})
def commands() -> None:
    logging.basicConfig(level=logging.INFO)


@commands.command("apply-script")
@click.option(
    "--host",
    "-h",
    nargs=1,
    required=False,
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
    "--output",
    "-o",
    nargs=1,
    required=False,
    type=str,
    help="Output study path",
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
    required=False,
    type=str,
    help="ID of the variant to apply the script onto",
)
@click.option(
    "--version",
    "-v",
    nargs=1,
    required=False,
    type=str,
    help=f"Study version. Default:{NEW_DEFAULT_STUDY_VERSION}",
    default=NEW_DEFAULT_STUDY_VERSION,
)
def cli_apply_script(
    input: str,
    study_id: Optional[str],
    output: Optional[str],
    host: Optional[str],
    auth_token: Optional[str],
    version: str,
) -> None:
    """Apply a variant script onto an AntaresWeb study variant"""
    if output is None and host is None:
        print("--output or --host must be set")
        exit(1)
    if output is not None and host is not None:
        print("only --output or --host must be set")
        exit(1)
    if host is not None and study_id is None:
        print("--study_id must be set")
        exit(1)

    res = generate_study(
        Path(input), study_id, output, host, auth_token, version
    )
    print(res)


@commands.command("generate-script")
@click.option(
    "--input",
    "-i",
    nargs=1,
    required=True,
    type=click.Path(exists=True),
    help="Study path",
)
@click.option(
    "--output",
    "-o",
    nargs=1,
    required=True,
    type=click.Path(exists=False),
    help="Script output path",
)
def cli_generate_script(input: str, output: str) -> None:
    """Generate variant script commands from a study"""
    extract_commands(Path(input), Path(output))


@commands.command("generate-script-diff")
@click.option(
    "--base",
    nargs=1,
    required=True,
    type=click.Path(exists=True),
    help="Base study path",
)
@click.option(
    "--variant",
    nargs=1,
    required=True,
    type=click.Path(exists=True),
    help="Variant study path",
)
@click.option(
    "--output",
    "-o",
    nargs=1,
    required=True,
    type=click.Path(exists=False),
    help="Script output path",
)
@click.option(
    "--version",
    "-v",
    nargs=1,
    required=False,
    type=str,
    help=f"Study version. Default:{NEW_DEFAULT_STUDY_VERSION}",
    default=NEW_DEFAULT_STUDY_VERSION,
)
def cli_generate_script_diff(
    base: str, variant: str, output: str, version: str
) -> None:
    """Generate variant script commands from two variant script directories"""
    generate_diff(Path(base), Path(variant), Path(output), version)


@commands.command("upgrade-study")
@click.argument(
    "study-path",
    nargs=1,
    type=click.Path(exists=True, dir_okay=True, readable=True, writable=True),
)
@click.argument(
    "target-version",
    nargs=1,
    type=click.STRING,
)
def cli_upgrade_study(study_path: Path, target_version: str) -> None:
    """Upgrades study version

    STUDY_PATH is the path of the study you want to update

    TARGET_VERSION is the version you want your study to be at (example 8.4.0 or 840)
    """
    upgrade_study(Path(study_path), target_version.replace(".", ""))


if __name__ == "__main__":
    commands()
