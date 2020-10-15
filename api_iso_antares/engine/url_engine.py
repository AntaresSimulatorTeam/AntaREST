from copy import deepcopy
from pathlib import Path
from typing import Tuple, Optional

from api_iso_antares.custom_exceptions import HtmlException
from api_iso_antares.custom_types import JSON, SUB_JSON


class UrlNotMatchJsonDataError(HtmlException):
    def __init__(self, message: str):
        super(UrlNotMatchJsonDataError, self).__init__(message, 404)


class UrlEngine:
    def __init__(self, jsonschema: JSON) -> None:
        self.jsonschema = jsonschema

    def apply(
        self, path: Path, json_data: JSON, depth: Optional[int] = None
    ) -> SUB_JSON:
        json_data = deepcopy(json_data)
        fragments = path.parts
        return self._apply_recursive(fragments, json_data, depth)

    @staticmethod
    def _apply_recursive(
        path: Tuple[str, ...], json_data: JSON, depth: Optional[int]
    ) -> SUB_JSON:
        if not path:
            if depth:
                UrlEngine.prune(json_data, max_depth=depth)
            return json_data

        key = path[0]

        if isinstance(json_data, list):
            search_element = [
                element for element in json_data if element["$id"] == key
            ]
            if not search_element:
                raise UrlNotMatchJsonDataError(f"Key {key} not in data.")
            new_jsondata = search_element[0]
        else:
            if key not in json_data:
                raise UrlNotMatchJsonDataError(f"Key {key} not in data.")
            new_jsondata = json_data[key]

        return UrlEngine._apply_recursive(path[1:], new_jsondata, depth)

    @staticmethod
    def prune(json_data: SUB_JSON, max_depth: int) -> None:
        if not isinstance(json_data, dict):
            return
        for key, value in json_data.items():
            if max_depth == 1:
                json_data[key] = None if isinstance(value, dict) else value
            else:
                UrlEngine.prune(value, max_depth - 1)
