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
import typing as t

import pydantic

ADAPTER: pydantic.TypeAdapter[t.Any] = pydantic.TypeAdapter(
    type=t.Any, config=pydantic.config.ConfigDict(ser_json_inf_nan="constants")
)  # ser_json_inf_nan="constants" means infinity and NaN values will be serialized as `Infinity` and `NaN`.


# These utility functions allow to serialize with pydantic instead of using the built-in python "json" library.
# Since pydantic v2 is written in RUST it's way faster.


def from_json(data: t.Union[str, bytes, bytearray]) -> t.Dict[str, t.Any]:
    return ADAPTER.validate_json(data)  # type: ignore


def to_json(data: t.Any, indent: t.Optional[int] = None) -> bytes:
    return ADAPTER.dump_json(data, indent=indent)


def to_json_string(data: t.Any, indent: t.Optional[int] = None) -> str:
    return to_json(data, indent=indent).decode("utf-8")


class AntaresBaseModel(pydantic.BaseModel):
    """
    Due to pydantic migration from v1 to v2, we can have this issue:

    class A(BaseModel):
        a: str

    A(a=2) raises ValidationError as we give an int instead of a str

    To avoid this issue we created our own BaseModel class that inherits from BaseModel and allows such object creation.
    """

    model_config = pydantic.config.ConfigDict(coerce_numbers_to_str=True)
