#!/usr/bin/python3
"""
Script used to update the version number and release date of AntaREST.
"""

import argparse
import datetime
import pathlib
import re
import typing

try:
    from antarest import __version__
except ImportError:
    __version__ = "(unknown): use the virtualenv's Python to get the actual version number."

# fmt: off
HERE = pathlib.Path(__file__).parent.resolve()
PROJECT_DIR = next(iter(p for p in HERE.parents if p.joinpath("antarest").exists()))
# fmt: on

TOKENS = [
    ("H1", r"^([^\n]+)\n={3,}$"),
    ("H2", r"^([^\n]+)\n-{3,}$"),
    ("H3", r"^#{3}\s+([^\n]+)$"),
    ("H4", r"^#{4}\s+([^\n]+)$"),
    ("LINE", r"^[^\n]+$"),
    ("NEWLINE", r"\n"),
    ("MISMATCH", r"."),
]

ANY_TOKEN_RE = "|".join([f"(?P<{name}>{regex})" for name, regex in TOKENS])


class Token:
    def __init__(self, kind: str, text: str) -> None:
        self.kind = kind
        self.text = text

    def __str__(self) -> str:
        return self.text


class NewlineToken(Token):
    def __init__(self) -> None:
        super().__init__("NEWLINE", "\n")


class TitleToken(Token):
    def __init__(self, kind: str, text: str) -> None:
        super().__init__(kind, text)

    @property
    def level(self) -> int:
        return int(self.kind[1:])

    def __str__(self) -> str:
        title = self.text.strip()
        if self.level == 1:
            return "\n".join([title, "=" * len(title)])
        elif self.level == 2:
            return "\n".join([title, "-" * len(title)])
        else:
            return "#" * self.level + " " + title


def parse_changelog(change_log: str) -> typing.Generator[Token, None, None]:
    for mo in re.finditer(ANY_TOKEN_RE, change_log, flags=re.MULTILINE):
        kind = mo.lastgroup
        if kind in {"H1", "H2", "H3", "H4"} and mo.lastindex is not None:
            title = mo[mo.lastindex + 1]
            yield TitleToken(kind, title)
        elif kind == "LINE":
            yield Token(kind, mo.group())
        elif kind == "NEWLINE":
            yield NewlineToken()
        else:
            raise NotImplementedError(kind, mo.group())


def update_changelog(
    change_log: str, new_version: str, new_date: str
) -> typing.Generator[Token, None, None]:
    title_found = False
    new_title = f"v{new_version} ({new_date})"
    for token in parse_changelog(change_log):
        if (
            not title_found
            and isinstance(token, TitleToken)
            and token.level == 2
        ):
            title_found = True
            if token.text != new_title:
                yield TitleToken(kind=token.kind, text=new_title)
                yield NewlineToken()
                yield NewlineToken()
                yield NewlineToken()
        yield token


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

    print("Preparing the CHANGELOG in the documentation...")
    changelog_path = PROJECT_DIR.joinpath("docs/CHANGELOG.md")
    change_log = changelog_path.read_text(encoding="utf-8")
    with changelog_path.open(mode="w", encoding="utf-8") as fd:
        for token in update_changelog(change_log, new_version, new_date):
            print(token, end="", file=fd)

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
