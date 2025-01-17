# Copyright (c) 2025, RTE (https://www.rte-france.com)
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

import os
import sys

# The Pyinstaller version we use has a known issue on windows and to fix it we need to implement this workaround.
# See issue description and workaround on pyinstaller website:
# https://pyinstaller.org/en/stable/common-issues-and-pitfalls.html#sys-stdin-sys-stdout-and-sys-stderr-in-noconsole-windowed-applications-windows-only
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

import argparse
import multiprocessing

from antarest import __version__
from antarest.core.cli import PathType


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--config",
        type=PathType(exists=True, file_ok=True),
        dest="config_file",
        help="path to the config file [default: '%(default)s']",
        default="./config.yaml",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        help="Display the server version and exit",
        version=__version__,
    )
    return parser.parse_args()


def main() -> None:
    """
    Entry point for "desktop" version of antares-web.

    This process actually only runs a small app which is accessible
    in the system tray.
    It spawns the actual server as a separate process.
    The systray app allows to shutdown the server, and to open
    antares webapp in the users's browser.
    """
    multiprocessing.freeze_support()

    arguments = parse_arguments()

    # VERY important to keep this import here in order to have fast startup
    # when only getting version
    from antarest.desktop.systray_app import run_systray_app

    run_systray_app(arguments.config_file)


if __name__ == "__main__":
    main()
