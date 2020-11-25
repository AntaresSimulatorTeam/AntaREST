import re
from copy import deepcopy
from pathlib import Path
from typing import Optional, Tuple

from api_iso_antares.custom_types import JSON, SUB_JSON
from api_iso_antares.jsm import JsonSchema


class UrlEngine:
    def __init__(self, jsm: JsonSchema) -> None:
        self.jsm = jsm

    @staticmethod
    def default_strategy(
        jsm: JsonSchema, part: str, path: Path
    ) -> Tuple[JsonSchema, Path]:
        jsm = jsm.get_child(key=part)
        path = path / part
        return jsm, path

    @staticmethod
    def output_strategy(
        jsm: JsonSchema, part: str, path: Path
    ) -> Tuple[JsonSchema, Path]:
        if part != "output":
            path = sorted(path.iterdir())[int(part) - 1]
            jsm = jsm.get_child()

        return jsm, path

    @staticmethod
    def output_links_strategy(
        jsm: JsonSchema, part: str, path: Path, url: str
    ) -> Tuple[JsonSchema, Path]:
        regex = re.search(re.escape(part) + r"/([^/]+)", url)
        second_node = regex.group(1) if regex else None
        path = path / f"{part} - {second_node}"
        return jsm.get_child(), path

    def resolve(self, url: str, path: Path) -> Tuple[JsonSchema, Path]:
        jsm = deepcopy(self.jsm)
        for part in url.split("/"):
            if jsm.get_strategy() in ["S12"]:
                jsm, path = self.output_strategy(jsm, part, path)
            else:
                jsm, path = self.default_strategy(jsm, part, path)
        return jsm, path

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
            new_jsondata = search_element[0]
        else:
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
