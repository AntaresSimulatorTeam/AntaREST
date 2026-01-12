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

from typing import Any, Dict

from antarest.core.serde import AntaresBaseModel
from antarest.core.serde.json import from_json, to_json


class IniProperties(
    AntaresBaseModel,
    # On reading, if the configuration contains an extra field, it is better
    # to forbid it, because it allows errors to be detected early.
    # Ignoring extra attributes can hide errors.
    extra="forbid",
    # If a field is updated on assignment, it is also validated.
    validate_assignment=True,
    # On testing, we can use snake_case for field names.
    populate_by_name=True,
):
    """
    Base class for configuration sections.
    """

    def to_config(self) -> Dict[str, Any]:
        """
        Convert the object to a dictionary for writing to a configuration file (`*.ini`).

        Returns:
            A dictionary with the configuration values.
        """

        config = {}
        for field_name, field in self.__class__.model_fields.items():
            value = getattr(self, field_name)
            if value is None:
                continue
            alias = field.alias
            assert alias is not None
            if isinstance(value, IniProperties):
                config[alias] = value.to_config()
            else:
                config[alias] = from_json(to_json(value))
        return config
