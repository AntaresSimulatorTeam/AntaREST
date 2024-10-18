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

from abc import ABC, abstractmethod

from antarest.core.serialization import AntaresBaseModel


class ICommandListener(ABC, AntaresBaseModel, extra="forbid"):
    """
    Interface for all listeners that can be given inside the `apply` method of a command.
    """

    @abstractmethod
    def notify_progress(self, progress: int) -> None:
        """
        Given a command progression, notifies the information.
        """
        raise NotImplementedError()
