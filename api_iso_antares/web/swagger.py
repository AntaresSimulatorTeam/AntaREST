from api_iso_antares.custom_types import JSON
from api_iso_antares import __version__


def update(swagger: JSON) -> JSON:
    # Set file format version
    del swagger["swagger"]
    swagger["openapi"] = "3.0.0"

    # Set head
    swagger["info"]["title"] = "API Antares"
    swagger["info"]["version"] = __version__

    return swagger
