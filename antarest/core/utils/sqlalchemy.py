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
from typing import Any, TypeVar

from sqlalchemy import inspect

T = TypeVar("T")


def clone_orm_object(cls: type[T], obj: T) -> T:
    mapper: Any = inspect(cls)
    data = {}
    for col in mapper.columns:
        data[col.key] = getattr(obj, col.key)
    return cls(**data)
