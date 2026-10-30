# Copyright (c) 2026, RTE (https://www.rte-france.com)
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
from antarest.core.serde import AntaresBaseModel


class OutputRawFolderTree(AntaresBaseModel):
    name: str
    files: list[str]
    directories: list["OutputRawFolderTree"]


class OutputRawFilesTree(AntaresBaseModel):
    """
    Tree structure of the files of an output, as written by the simulator.
    """

    files: list[str]
    directories: list[OutputRawFolderTree]
