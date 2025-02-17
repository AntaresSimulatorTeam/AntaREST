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

"""
This modules hosts technical components related to serializing and deserializing,
for various formats: INI, JSON, ...
"""
import typing as t

import pydantic


class AntaresBaseModel(pydantic.BaseModel):
    """
    Due to pydantic migration from v1 to v2, we can have this issue:

    class A(BaseModel):
        a: str

    A(a=2) raises ValidationError as we give an int instead of a str

    To avoid this issue we created our own BaseModel class that inherits from BaseModel and allows such object creation.
    """

    model_config = pydantic.config.ConfigDict(coerce_numbers_to_str=True)
