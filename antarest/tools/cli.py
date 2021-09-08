from pathlib import Path

import click


@click.group()
def commands() -> None:
    pass


@commands.command()
@click.option(
    "--host",
    "-h",
    nargs=1,
    required=True,
    help="Host URL of the antares web instance",
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
    help="ID of the variant to apply the script onto",
)
def apply_script(host: str, input: Path, study_id: str) -> None:
    """Apply a variant script onto an AntaresWeb study variant"""
    print(f"{host}, {input}, {study_id}")


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
def generate_script(input: Path, output: Path) -> None:
    """Generate variant script commands from a study or study fragment"""
    print(f"{input}, {output}")


if __name__ == "__main__":
    commands()
