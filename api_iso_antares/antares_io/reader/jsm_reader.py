from pathlib import Path

import jsonref

from api_iso_antares.antares_io.jsonschema import JsonSchema


class JsmReader:
    @staticmethod
    def read(path: Path) -> JsonSchema:
        data = jsonref.load_uri(path.resolve().as_uri())
        jsm = JsonSchema(data)
        return jsm
