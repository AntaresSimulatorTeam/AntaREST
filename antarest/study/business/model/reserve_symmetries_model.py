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
from typing import Annotated, TypeAlias

from pydantic import BeforeValidator

from antarest.study.business.model.reserve_definition_model import ReserveDefinitionId


def _symmetry_validator(data: list[str]) -> list[str]:
    if len(data) < 2:
        raise ValueError(f"Reserve symmetries should have at least 2 elements, and was {data}")
    if len(set(data)) != len(data):
        raise ValueError(f"Reserve symmetries should not contain duplicates, and was {data}")
    return data


ReserveSymmetry: TypeAlias = Annotated[list[ReserveDefinitionId], BeforeValidator(_symmetry_validator)]
ReserveSymmetries: TypeAlias = Annotated[list[ReserveSymmetry], BeforeValidator(lambda x: sorted(x))]
