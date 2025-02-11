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

from typing import Dict, List, Tuple

from fastapi import FastAPI
from fastapi.openapi.models import Example
from fastapi.routing import APIRoute

sim = "{sim} = simulation index <br/>"
area = "{area} = area name to select <br/>"
link = "{link} = link name to select <br/>"
attachment = "User-defined file attachment <br/>"

# noinspection SpellCheckingInspection
urls: List[Tuple[str, str]] = [
    ("layers/layers", ""),
    ("settings/generaldata", ""),
    ("output/{sim}/about-the-study/parameters", sim),
    ("output/{sim}/about-the-study/study", sim),
    ("output/{sim}/info(.antares-output)", sim),
    ("input/areas/{area}/optimization", area),
    ("input/areas/{area}/ui", area),
    ("input/bindingconstraints/bindingconstraints", ""),
    ("input/hydro/hydro", ""),
    ("input/links/{area}/properties/{link}", area + link),
    ("input/load/prepro/{area}/settings", area),
    ("input/solar/prepro/{area}/settings", area),
    ("input/thermal/clusters/{area}/list", area),
    ("input/thermal/areas", ""),
    ("input/wind/prepro/{area}/settings", area),
    ("user/wind_solar/synthesis_windSolar.xlsx", attachment),
]


def get_path_examples() -> Dict[str, Example]:
    return {url: {"value": url, "description": des} for url, des in urls}


def customize_openapi(app: FastAPI) -> None:
    for route in app.routes:
        if isinstance(route, APIRoute):
            route.operation_id = route.name
