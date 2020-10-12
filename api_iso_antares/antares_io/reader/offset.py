from pathlib import Path
from typing import List

from api_iso_antares.custom_types import JSON, SUB_JSON


class Offset:
    def __init__(self, path: Path, json_data: JSON, jsm: JSON) -> None:
        self.path = path
        self.json_data = json_data
        self.jsm = jsm

    def set_data(self, key: str, value: SUB_JSON) -> None:
        self.json_data[key] = value

    def get_jsm_keys(self) -> List[str]:
        if "properties" not in self.jsm:
            pass
        return self.jsm["properties"].keys()
        #return [
        #    key
        #    for key in self.jsm["properties"].keys()
        #    if key != "name"
        #]

    def next(self, key):
        if self.jsm["type"] == "object":
            jsm = self.jsm["properties"]
        elif self.jsm["type"] == "array":
            jsm = self.jsm["items"]
        return Offset(path=self.path / key, json_data=None, jsm=jsm)
