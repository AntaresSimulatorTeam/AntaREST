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

from pydantic import StringConstraints

# A string without new lines. This ensures that it's safe to log it, see sonar issue python:S5145
SanitizedStr: TypeAlias = Annotated[str, StringConstraints(pattern=r"^.*$")]

# A string containing only valid characters for file names (no "/")
FileNameStr: TypeAlias = Annotated[str, StringConstraints(pattern=r"^[^/]*$")]

# Specific string type for UUIDs
UuidStr: TypeAlias = Annotated[
    str, StringConstraints(pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
]
