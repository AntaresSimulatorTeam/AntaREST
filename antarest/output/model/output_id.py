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
import re
from typing import Annotated

from pydantic import AfterValidator

# An output id names a direct child of the outputs folder: one segment, not "", "." or "..", with no
# separator ("/", "\"), drive qualifier (":") or line break. Anything else escapes the folder (path
# traversal, CWE-22/23) and, for database studies with side-by-side outputs, another study's (CWE-639).
# On Windows ":" matters: "C:" is drive-relative and joins to the outputs folder itself.
_OUTPUT_ID_PATTERN = re.compile(r"\A(?!\.\.?\Z)[^/\\:\r\n]+\Z")


def is_valid_output_id(output_id: str) -> bool:
    return _OUTPUT_ID_PATTERN.match(output_id) is not None


def _validate_output_id(output_id: str) -> str:
    if not is_valid_output_id(output_id):
        raise ValueError("An output id must name a direct child of the study outputs folder")
    return output_id


# Validated at the API edge: an invalid output id is rejected with a 422 before reaching the service.
OutputId = Annotated[str, AfterValidator(_validate_output_id)]
