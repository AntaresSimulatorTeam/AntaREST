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

from pathlib import Path
from typing import cast

from typing_extensions import override


class BaseConfigError(Exception):
    """Base class of the configuration errors."""


class SimulationParsingError(BaseConfigError):
    def __init__(self, output_path: Path, reason: str):
        super().__init__(output_path, reason)

    @property
    def output_path(self) -> Path:
        return cast(Path, self.args[0])

    @property
    def reason(self) -> str:
        return cast(str, self.args[1])

    @override
    def __str__(self) -> str:
        output_path = self.output_path
        reason = self.reason
        return f"Fail to parse the simulation file '{output_path}': {reason}"


class XpansionParsingError(BaseConfigError):
    def __init__(self, xpansion_json: Path, reason: str):
        super().__init__(xpansion_json, reason)

    @property
    def xpansion_json(self) -> Path:
        return cast(Path, self.args[0])

    @property
    def reason(self) -> str:
        return cast(str, self.args[1])

    @override
    def __str__(self) -> str:
        xpansion_json = self.xpansion_json
        reason = self.reason
        return f"Fail to parse the Xpansion file '{xpansion_json}': {reason}"
