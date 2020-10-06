from typing import List

from api_iso_antares.custom_types import JSON, SUB_JSON


class UrlEngine:
    def __init__(self):
        pass

    def apply(self, path: str, jsonschema: JSON, json_data: JSON) -> SUB_JSON:
        fragments = path.split("/")
        return self._apply(fragments, json_data)

    @staticmethod
    def _apply(path: List[str], json_data: JSON) -> SUB_JSON:
        if not path or json_data is None:
            return json_data
        return UrlEngine._apply(path[1:], json_data.get(path[0], None))
