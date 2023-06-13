#!/usr/bin/python3
"""
Script used to update the version number and release date of AntaREST.
"""

import argparse
import datetime
import pathlib
import re

try:
    from antarest import __version__
except ImportError:
    __version__ = "(unknown): use the virtualenv's Python to get the actual version number."

# fmt: off
HERE = pathlib.Path(__file__).parent.resolve()
PROJECT_DIR = next(iter(p for p in HERE.parents if p.joinpath("antarest").exists()))
# fmt: on


def upgrade_version(new_version: str, new_date: str) -> None:
    """
    Update the version number and release date in specific files.

    Args:
        new_version: The new version number to update.
        new_date: The new release date to update.

    Returns:

    """
    # Patching version number
    files_to_patch = [
        (
            "setup.py",
            "version=.*",
            f'version="{new_version}",',
        ),
        (
            "sonar-project.properties",
            "sonar.projectVersion=.*",
            f"sonar.projectVersion={new_version}",
        ),
        (
            "antarest/__init__.py",
            "__version__ =.*",
            f'__version__ = "{new_version}"',
        ),
        (
            "webapp/package.json",
            '"version":.*',
            f'"version": "{new_version}",',
        ),
        (
            "webapp/package-lock.json",
            '"version":.*',
            f'"version": "{new_version}",',
        ),
    ]
    print(f"Updating files to version {new_version}...")
    for rel_path, search, replace in files_to_patch:
        fullpath = PROJECT_DIR.joinpath(rel_path)
        if fullpath.is_file():
            print(f"- updating '{fullpath.relative_to(PROJECT_DIR)}'...")
            text = fullpath.read_text(encoding="utf-8")
            patched = re.sub(search, replace, text, count=1)
            fullpath.write_text(patched, encoding="utf-8")

    # Patching release date
    search = "__date__ =.*"
    replace = f'__date__ = "{new_date}"'

    print(f"Updating the release date to {new_date}...")
    fullpath = PROJECT_DIR.joinpath("antarest/__init__.py")
    text = fullpath.read_text(encoding="utf-8")
    patched = re.sub(search, replace, text, count=1)
    fullpath.write_text(patched, encoding="utf-8")

    print("The version has been successfully updated.")


class RegexType:
    """
    Type of un argument which is checked by a regex.
    """

    def __init__(self, regex: str) -> None:
        self.regex = re.compile(regex)

    def __call__(self, string: str) -> str:
        if self.regex.fullmatch(string):
            return string
        pattern = self.regex.pattern
        msg = f"Invalid value '{string}': it doesn't match '{pattern}'"
        raise argparse.ArgumentTypeError(msg)


DESCRIPTION = """\
Upgrade the version number and release date of AntaREST.

Use this script to update the version number and release date of the AntaREST application.
It is designed to be executed before releasing the application on GitHub, specifically
when a new version is completed in the `master` branch or `hotfix` branch.
"""


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="upgrade_version", description=DESCRIPTION
    )
    parser.add_argument(
        "--version",
        dest="new_version",
        action="version",
        version=__version__,
        help="show the current version and exit",
    )
    date_type = RegexType(regex=r"\d{4}-\d{2}-\d{2}")
    parser.add_argument(
        "-d",
        "--date",
        dest="new_date",
        type=date_type,
        default=datetime.date.today().isoformat(),
        help=f"new release date, using the format '{date_type.regex.pattern}'",
        metavar="ISO_DATE",
    )
    version_type = RegexType(regex=r"\d+(?:\.\d+)+")
    parser.add_argument(
        "new_version",
        type=version_type,
        help=f"new application version, using the format '{version_type.regex.pattern}'",
        metavar="VERSION",
    )

    args = parser.parse_args()
    upgrade_version(args.new_version, args.new_date)


if __name__ == "__main__":
    main()
