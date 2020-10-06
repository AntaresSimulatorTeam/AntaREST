from typing import List

from api_iso_antares.types import JSON, SUB_JSON


class UrlEngine:
    def __init__(self, jsonschema: JSON, json_data: JSON):
        self.jsonschema = jsonschema
        self.json_data = json_data

    def apply(self, path: str) -> SUB_JSON:
        fragments = path.split("/")
        return self._apply(fragments, self.json_data)

    @staticmethod
    def _apply(path: List[str], json_data: JSON) -> SUB_JSON:
        if not path or json_data is None:
            return json_data
        return UrlEngine._apply(path[1:], json_data.get(path[0], None))
