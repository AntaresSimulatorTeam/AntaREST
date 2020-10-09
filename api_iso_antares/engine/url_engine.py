from pathlib import Path
from typing import List, Tuple

from api_iso_antares.custom_exceptions import HtmlException
from api_iso_antares.custom_types import JSON, SUB_JSON


class UrlNotMatchJsonDataError(HtmlException):
    def __init__(self, message: str):
        super(UrlNotMatchJsonDataError, self).__init__(message, 404)


class UrlEngine:
    def __init__(self, jsonschema: JSON) -> None:
        self.jsonschema = jsonschema

    def apply(self, path: Path, json_data: JSON, depth: int) -> SUB_JSON:
        fragments = path.parts
        return self._apply_recursive(fragments, json_data)

    @staticmethod
    def _apply_recursive(path: Tuple[str, ...], json_data: JSON) -> SUB_JSON:
        if not path:
            return json_data

        key = path[0]
        if key not in json_data:
            raise UrlNotMatchJsonDataError(f"Key {key} not in data.")

        return UrlEngine._apply_recursive(path[1:], json_data[key])
