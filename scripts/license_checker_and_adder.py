import glob
import os
from pathlib import Path
import typing as t
import click


@click.command("license_checker_and_adder")
@click.option(
    "--path",
    nargs=1,
    required=False,
    type=str,
    default=None,
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
def cli(path: t.Optional[Path], action: str) -> None:
    if not path:
        path = Path(__file__).parent
    if action not in ["check", "fix"]:
        raise ValueError(f"Parameter --action should be either 'check' or 'fix' and was '{action}'")

    license_header = """# Copyright (c) 2024, RTE (https://www.rte-france.com)
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
    license_as_list = license_header.splitlines()
    license_to_save = [header + "\n" for header in license_as_list]
    license_to_save.append("\n")

    file_count = 0
    all_files_and_folder = glob.glob(os.path.join(path, "**"), recursive=True)
    for file in all_files_and_folder:
        file_path = Path(file)
        if not file_path.is_file():
            continue
        if file_path.suffixes != ['.py']:
            continue
        file_content = file_path.read_text().splitlines()
        if len(file_content) < 11 or file_content[:11] != license_as_list:
            file_count += 1
            click.echo(f"{file_path.relative_to(path)} has no valid header.")
            new_lines = []
            if action == "fix":
                with open(file_path, "r") as f:  # doesn't seem really optimal as I read the file twice.
                    already_licensed = False
                    lines = f.readlines()
                    first_line = lines[0].lower() if len(lines) > 0 else []
                    if "copyright" in first_line or "license" in first_line:  # assumes license follows this
                        already_licensed = True
                    if already_licensed: # I don't really know what to do here
                        raise ValueError(f'File {file_path.relative_to(path)} already licensed.')
                    else:
                        new_lines = license_to_save + lines
            if new_lines:
                with open(file_path, "w") as f:
                    f.writelines(new_lines)
    if file_count > 0:
        if action == "fix":
            click.echo(f"{file_count} files have been fixed")
        else:
            click.echo(f"{file_count} files have an invalid header. Use --action=fix to fix them")
    else:
        click.echo("All good !")

def main():
    cli(prog_name="cli")


if __name__ == '__main__':
    main()
