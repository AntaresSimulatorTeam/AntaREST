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

from typing import Any

from pydantic import BaseModel


def get_model_field_values(model: BaseModel) -> dict[str, Any]:
    """
    Returns a shallow copy dictionary of the fields of a model.

    Allows to get fields without performing a full, recursive, model_dump.
    """
    return {f: getattr(model, f) for f in model.__class__.model_fields.keys()}
