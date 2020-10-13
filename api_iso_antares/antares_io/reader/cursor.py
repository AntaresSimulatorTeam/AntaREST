from pathlib import Path
from typing import List, Any, Tuple

from api_iso_antares.custom_exceptions import HtmlException
from api_iso_antares.custom_types import JSON


class PathNotMatchJsonSchema(HtmlException):
    def __init__(self, message: str) -> None:
        super(PathNotMatchJsonSchema, self).__init__(message, 405)


class JsmCursor:
    def __init__(self, jsm: JSON, type_data: str = "object"):
        self.jsm = jsm
        self.type_data = type_data

    def get_properties(self) -> List[str]:
        return [
            key for key in self.jsm["properties"].keys() if not (key == "name")
        ]

    def next(self, key: str) -> "JsmCursor":
        attr = self.jsm["properties"][key]
        if attr["type"] == "array":
            return JsmCursor(attr["items"], type_data="array")
        else:
            return JsmCursor(attr, type_data=attr["type"])

    def get_type(self) -> str:
        return self.type_data


class DataCursor:
    def __init__(self, data: Any, jsm: JsmCursor):
        self.data = data
        self.jsm = jsm

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value

    def next(self, key: str) -> "DataCursor":
        next_jsm = self.jsm.next(key)
        self.data[key] = [] if next_jsm.get_type() == "array" else {}
        return DataCursor(self.data[key], next_jsm)

    def next_item(self, key: str) -> "DataCursor":
        self.data.append({"name": key})
        return DataCursor(self.data[-1], self.jsm)

    def get_properties(self) -> List[str]:
        return self.jsm.get_properties()

    def get_type(self) -> str:
        return self.jsm.get_type()

    def is_array(self) -> bool:
        return self.get_type() == "array"

    def is_object(self) -> bool:
        return self.get_type() == "object"


class PathCursor:
    def __init__(self, path: Path):
        self.path = path
        PathCursor.check_path(path)

    def next(self, key: str) -> "PathCursor":
        path = self.path / key

        return PathCursor(path)

    def is_dir(self) -> bool:
        return self.path.is_dir()

    def next_items(self) -> List[Tuple["PathCursor", str]]:
        return [
            (PathCursor(path), path.name)
            for path in sorted(self.path.iterdir())
        ]

    @staticmethod
    def check_path(path) -> None:
        if not path.exists():
            raise PathNotMatchJsonSchema(f"{path} not in study.")
