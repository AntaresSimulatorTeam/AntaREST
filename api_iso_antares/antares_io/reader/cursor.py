from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from api_iso_antares.custom_exceptions import HtmlException
from api_iso_antares.custom_types import JSON


class PathNotMatchJsonSchema(HtmlException):
    def __init__(self, message: str) -> None:
        super(PathNotMatchJsonSchema, self).__init__(message, 405)


class JsmCursor:
    def __init__(
        self, jsm: JSON, type_data: str = "object", origin: JSON = {}
    ):
        self.jsm = jsm
        self.type_data = type_data
        self.origin = origin or self.jsm

    def get_properties(self) -> List[str]:
        return [
            key for key in self.jsm["properties"].keys() if not (key == "$id")
        ]

    def next(self, key: str) -> "JsmCursor":
        sub_jsm = self.jsm["properties"][key]
        if sub_jsm["type"] == "array":
            return JsmCursor(
                sub_jsm["items"], type_data="array", origin=self.origin
            )
        else:
            return JsmCursor(
                sub_jsm, type_data=sub_jsm["type"], origin=self.origin
            )

    def get_type(self) -> str:
        return self.type_data

    def get_metadata(self) -> Optional[JSON]:
        return self.jsm.get("rte-metadata", None)

    def get_filename(self) -> Optional[str]:
        metadata = self.get_metadata()
        filename: Optional[str] = None
        if metadata is not None:
            filename = metadata.get("filename", None)
        return filename

    def is_array(self) -> bool:
        return self.get_type() == "array"

    def is_object(self) -> bool:
        return self.get_type() == "object"


class DataCursor:
    def __init__(self, data: Any):
        self.data = data

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value

    def next(self, key: str, jsm: JsmCursor) -> "DataCursor":
        self.data[key] = [] if jsm.get_type() == "array" else {}
        return DataCursor(self.data[key])

    def next_item(self, key: str) -> "DataCursor":
        self.data.append({"$id": key})
        return DataCursor(self.data[-1])


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
    def check_path(path: Path) -> None:
        if not path.exists():
            raise PathNotMatchJsonSchema(f"{path} not in study.")
