from typing import Any, List, Tuple

from fastapi import FastAPI
from fastapi.routing import APIRoute

sim = "{sim} = simulation index <br/>"
area = "{area} = area name to select <br/>"
link = "{link} = link name to select <br/>"

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
]


def get_path_examples() -> Any:
    examples = {url: {"value": url, "description": des} for url, des in urls}
    return examples


def customize_openapi(app: FastAPI) -> None:
    for route in app.routes:
        if isinstance(route, APIRoute):
            route.operation_id = route.name
