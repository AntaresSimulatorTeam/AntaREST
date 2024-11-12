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
from pydantic import ConfigDict

from antarest.core.serialization import AntaresBaseModel
from antarest.core.utils.string import to_camel_case, to_kebab_case


class LoadDTO(AntaresBaseModel):
    matrix: bytes

    model_config = ConfigDict(alias_generator=to_camel_case, extra="forbid")

    def to_properties(self) -> "LoadProperties":
        return LoadProperties(matrix=self.matrix)


class LoadProperties(AntaresBaseModel):
    matrix: bytes

    model_config = ConfigDict(alias_generator=to_kebab_case, extra="forbid")

    def to_dto(self) -> LoadDTO:
        return LoadDTO(matrix=self.matrix)
