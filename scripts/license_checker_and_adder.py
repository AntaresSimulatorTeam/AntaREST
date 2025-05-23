import os
import re
from pathlib import Path
from typing import List

import click

# Use to skip subtrees that have their own licenses (forks)
LICENSE_FILE_PATTERN = re.compile("LICENSE.*")

BACKEND_LICENSE_HEADER = """# Copyright (c) 2025, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.
"""


front_license_path = Path(__file__).resolve().parent.parent / "webapp" / "license-header.js"
FRONTEND_LICENSE_HEADER = front_license_path.read_text()


def is_license_file(filename: str) -> bool:
    return LICENSE_FILE_PATTERN.match(filename) is not None


def check_file(file_path: Path, action: str, license_as_list: List[str], license_to_save: List[str]) -> bool:
    file_content = file_path.read_text().splitlines()
    n = len(license_as_list)
    if len(file_content) >= n and file_content[:n] == license_as_list:
        return True
    click.echo(f"{file_path} has no valid header.")
    new_lines = []
    if action == "fix":
        with open(file_path, "r") as f:  # doesn't seem really optimal as I read the file twice.
            already_licensed = False
            lines = f.readlines()
            first_line = lines[0].lower() if len(lines) > 0 else []
            if "copyright" in first_line or "license" in first_line:  # assumes license follows this
                already_licensed = True
            if already_licensed:  # I don't really know what to do here
                raise ValueError(f"File {file_path} already licensed.")
            else:
                new_lines = license_to_save + lines
    if new_lines:
        with open(file_path, "w") as f:
            f.writelines(new_lines)


def check_dir(
    cwd: Path,
    dir_path: Path,
    action: str,
    invalid_files: List[Path],
    suffixes: List[str],
    license_as_list: List[str],
    license_to_save: List[str],
) -> None:
    _, dirnames, filenames = next(os.walk(dir_path))
    for f in filenames:
        if dir_path != cwd and is_license_file(f):
            click.echo(f"Found third party license file, skipping folder: {dir_path / f}")
            return

    for f in filenames:
        file_path = dir_path / f

        if file_path.suffix not in suffixes:
            continue

        if not check_file(file_path, action, license_as_list, license_to_save):
            invalid_files.append(file_path)

    for d in dirnames:
        check_dir(cwd, dir_path / d, action, invalid_files, suffixes, license_as_list, license_to_save)


@click.command("license_checker_and_adder")
@click.option(
    "--path",
    nargs=1,
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to check",
)
@click.option(
    "--action",
    nargs=1,
    required=False,
    default="check",
    type=str,
    help="Action to realise. Can either be check or fix",
)
def cli(path: Path, action: str) -> None:
    if action not in ["check", "check-strict", "fix"]:
        raise ValueError(f"Parameter --action should be 'check', 'check-strict' or 'fix' and was '{action}'")

    invalid_files = []
    cwd = Path.cwd()
    # --------- infer which files to check and which license to add
    suffixes = [".ts", ".tsx"]
    license_header = FRONTEND_LICENSE_HEADER
    if path.name in ["antarest", "tests"]:
        suffixes = [".py"]
        license_header = BACKEND_LICENSE_HEADER
    license_as_list = license_header.splitlines()
    license_to_save = [header + "\n" for header in license_as_list] + ["\n"]
    # --------
    check_dir(cwd, path, action, invalid_files, suffixes, license_as_list, license_to_save)
    file_count = len(invalid_files)
    if file_count > 0:
        if action == "fix":
            click.echo(f"{file_count} files have been fixed")
        else:
            click.echo(f"{file_count} files have an invalid header. Use --action=fix to fix them")
            if action == "check-strict":
                raise ValueError("Some files have invalid headers")

    else:
        click.echo("All good !")


def main():
    cli(prog_name="cli")


if __name__ == "__main__":
    main()
