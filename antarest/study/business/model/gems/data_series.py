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

from pydantic import ConfigDict

from antarest.core.serde import AntaresBaseModel
from antarest.core.serde.np_array import NpArray


class GemsDataSeries(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", arbitrary_types_allowed=True)

    id: str
    values: NpArray
