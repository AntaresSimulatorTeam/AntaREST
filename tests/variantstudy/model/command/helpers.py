# Copyright (c) 2024, RTE (https://www.rte-france.com)
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

from pathlib import Path


def reset_line_separator(*paths: Path):
    """
    Reset the line separator of a text file to use the system default line separator (CR+LF on Windows).

    This utility function is used to avoid false negative in directory checksum comparison.
    The idea is to normalize text files before calculating the checksum to avoid differences in newline.

    Directory checksum is done with `checksumdir.dirhash` which performs binary file reading.
    """
    for path in paths:
        path.write_text(path.read_text())
