from pathlib import Path

from api_iso_antares.custom_types import JSON, SUB_JSON


class Offset:
    def __init__(self, path: Path, json_data: JSON, jsm: JSON) -> None:
        self.path = path
        self.json_data = json_data
        self.jsm = jsm

    def set_data(self, key: str, value: SUB_JSON) -> None:
        self.json_data[key] = value

    def get_properties(self):
        return {
            key: value
            for key, value in self.jsm["properties"].items()
            if key != "name"
        }

    def next(self, key):
        pass
