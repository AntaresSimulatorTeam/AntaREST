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
from antarest.study.business.model.xpansion_model import XpansionResourceFileType


def get_resource_dir(resource_type: XpansionResourceFileType) -> list[str]:
    if resource_type == XpansionResourceFileType.CONSTRAINTS:
        return ["user", "expansion", "constraints"]
    elif resource_type == XpansionResourceFileType.CAPACITIES:
        return ["user", "expansion", "capa"]
    elif resource_type == XpansionResourceFileType.WEIGHTS:
        return ["user", "expansion", "weights"]
    raise NotImplementedError(f"resource_type '{resource_type}' not implemented")
