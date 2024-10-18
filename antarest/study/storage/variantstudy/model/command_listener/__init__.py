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
from abc import ABC

from antarest.core.serialization import AntaresBaseModel


class ICommandListener(ABC, AntaresBaseModel, extra="forbid", arbitrary_types_allowed=True):
    """
    Interface for all commands that can be applied to a study.

    Attributes:
        command_id: The ID of the command extracted from the database, if any.
        command_name: The name of the command.
        version: The version of the command (currently always equal to 1).
        command_context: The context of the command.
    """
