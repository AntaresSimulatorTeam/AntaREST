from typing import Any, List, Tuple

from flask import request, jsonify
from flask_swagger import swagger  # type: ignore

from antarest.common.custom_types import JSON
from antarest import __version__


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


def _add_examples(swagger: JSON) -> None:
    endpoint = "/studies/{path}"
    examples = {url: {"value": url, "description": des} for url, des in urls}

    swagger["paths"][endpoint]["get"]["parameters"][1]["examples"] = examples
    swagger["paths"][endpoint]["post"]["parameters"][1]["examples"] = examples
    swagger["paths"]["/studies/{uuid}/{path}"] = swagger["paths"][endpoint]
    del swagger["paths"][endpoint]


def _add_post_file_body(swagger: JSON) -> None:
    swagger["paths"]["/file/{path}"]["post"]["requestBody"] = {
        "description": "Send text file to server",
        "required": True,
        "content": {
            "multipart/form-data": {
                "schema": {
                    "type": "object",
                    "required": ["matrix"],
                    "properties": {
                        "matrix": {"type": "string", "format": "binary"}
                    },
                }
            }
        },
    }


def _add_post_import_body(swagger: JSON) -> None:
    swagger["paths"]["/studies"]["post"]["requestBody"] = {
        "description": "Import study to server",
        "required": True,
        "content": {
            "multipart/form-data": {
                "schema": {
                    "type": "object",
                    "required": ["study"],
                    "properties": {
                        "study": {"type": "string", "format": "binary"}
                    },
                }
            }
        },
    }


def _add_post_edit_study(swagger: JSON) -> None:
    swagger["paths"]["/studies/{uuid}/{path}"]["post"]["requestBody"] = {
        "description": "Import study to server",
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                }
            }
        },
    }


def _update(swagger: JSON) -> JSON:
    # Set file format version
    del swagger["swagger"]
    swagger["openapi"] = "3.0.0"

    # Set head
    swagger["info"]["title"] = "API Antares"
    swagger["info"]["version"] = __version__

    # Add dynamics path
    _add_examples(swagger)

    # Add request body
    _add_post_edit_study(swagger)
    _add_post_file_body(swagger)
    _add_post_import_body(swagger)

    return swagger


def build_swagger(application: Any) -> None:
    @application.route(  # type: ignore
        "/swagger.json",
        methods=["GET"],
    )
    def spec() -> Any:
        specification = _update(swagger(application))
        specification["servers"] = [{"url": request.url_root}]

        return jsonify(specification)
