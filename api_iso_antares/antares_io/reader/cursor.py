from pathlib import Path
from typing import List, Any, Tuple

from api_iso_antares.custom_exceptions import HtmlException
from api_iso_antares.custom_types import JSON, SUB_JSON


class PathNotMatchJsonSchema(HtmlException):
    def __init__(self, message: str) -> None:
        super(PathNotMatchJsonSchema, self).__init__(message, 405)

class JsmCursor:
    def __init__(self, jsm: JSON, type_data: str = "object"):
        self.jsm = jsm
        self.type_data = type_data

    def get_properties(self) -> List[str]:
        return [
            key
            for key in self.jsm["properties"].keys()
            if not (key == 'name')
        ]

    def next(self, key: str) -> "JsmCursor":
        attr = self.jsm['properties'][key]
        if attr["type"] == "array":
            return JsmCursor(attr["items"], type_data="array")
        else:
            return JsmCursor(attr, type_data=attr["type"])

    def get_type(self) -> str:
        return self.type_data


class DataCursor:
    def __init__(self, data: Any):
        self.data = data

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value

    def next(self, key: str, data_type: str = "object") -> "DataCursor":
        self.data[key] = [] if data_type == "array" else {}
        return DataCursor(self.data[key])

    def next_item(self, id: str) -> "DataCursor":
        self.data.append({"name": id})
        return DataCursor(self.data[-1])


class PathCursor:
    def __init__(self, path: Path):
        self.path = path

    def next(self, key: str) -> "PathCursor":
        path = self.path / key

        if not path.exists():
            raise PathNotMatchJsonSchema(
                f"{path} not in study."
            )
        return PathCursor(path)

    def is_dir(self) -> bool:
        return self.path.is_dir()

    def next_items(self) -> List[Tuple["PathCursor", str]]:
        return [
            (PathCursor(path), path.name)
            for path in sorted(self.path.iterdir())
        ]
