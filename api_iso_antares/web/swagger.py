from typing import List, Tuple

from api_iso_antares.custom_types import JSON
from api_iso_antares import __version__

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


def update(swagger: JSON) -> JSON:
    # Set file format version
    del swagger["swagger"]
    swagger["openapi"] = "3.0.0"

    # Set head
    swagger["info"]["title"] = "API Antares"
    swagger["info"]["version"] = __version__

    # Add dynmatic path
    url = "/studies/{path}"
    examples = {
        value: {"value": value, "description": des} for value, des in urls
    }

    print(list(swagger["paths"][url]))
    swagger["paths"][url]["get"]["parameters"][1]["examples"] = examples
    swagger["paths"][url]["post"]["parameters"][1]["examples"] = examples
    swagger["paths"]["/studies/{uuid}/{path}"] = swagger["paths"][url]
    del swagger["paths"][url]

    return swagger
