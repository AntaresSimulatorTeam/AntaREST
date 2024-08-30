# Copyright (c) 2024, RTE (https://www.rte-france.com)
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

def to_pascal_case(value: str) -> str:
    return "".join(word.capitalize() for word in value.split("_"))


def to_camel_case(value: str) -> str:
    v = to_pascal_case(value)
    return v[0].lower() + v[1:] if len(v) > 0 else ""
