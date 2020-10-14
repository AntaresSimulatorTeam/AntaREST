import os
from copy import deepcopy
from pathlib import Path

from jsonschema import validate

from api_iso_antares.antares_io.reader.cursor import (
    PathCursor,
    JsmCursor,
    DataCursor,
)
from api_iso_antares.antares_io.reader.ini_reader import IniReader
from api_iso_antares.antares_io.validator.jsonschema import JsmValidator
from api_iso_antares.custom_exceptions import HtmlException
from api_iso_antares.custom_types import JSON, SUB_JSON


class PathNotMatchJsonSchema(HtmlException):
    def __init__(self, message: str) -> None:
        super(PathNotMatchJsonSchema, self).__init__(message, 405)


class FolderReaderEngine:
    def __init__(
        self,
        reader_ini: IniReader,
        jsonschema: JSON,
        root: Path,
        jsm_validator: JsmValidator,
    ):
        self._reader_ini = reader_ini
        self.jsonschema = jsonschema
        self.root = root
        self.jsm_validator = jsm_validator

    def read(self, folder: Path) -> JSON:
        jsonschema = deepcopy(self.jsonschema)
        output: JSON = dict()

        data_cursor = DataCursor(output, JsmCursor(jsonschema))
        path_cursor = PathCursor(folder)
        self._parse_recursive(path_cursor, data_cursor)

        self.validate(output)

        return output

    def _parse_recursive(
        self, path_cursor: PathCursor, data_cursor: DataCursor
    ) -> None:
        for key in data_cursor.get_properties():
            next_path = path_cursor.next(key)
            next_data = data_cursor.next(key)

            if next_path.is_dir():
                self._parse_dir(next_path, next_data)
            else:
                data_cursor.set(key, self._parse_file(next_path))

    def _parse_dir(self, path: PathCursor, data: DataCursor) -> None:
        if data.is_object():
            self._parse_recursive(path, data)
        elif data.is_array():
            for path, key in path.next_items():
                self._parse_recursive(path, data.next_item(key))

    def _parse_file(self, cursor: PathCursor) -> SUB_JSON:
        path = cursor.path
        if path.suffix == ".txt":
            path_parent = f"{self.root}{os.sep}"
            relative_path = str(path).replace(path_parent, "")
            return f"matrices{os.sep}{relative_path}"
        elif path.suffix == ".ini":
            return self._reader_ini.read(path)
        raise NotImplementedError(
            f"File extension {path.suffix} not implemented"
        )

    def validate(self, jsondata: JSON) -> None:
        if (not self.jsonschema) and jsondata:
            raise ValueError("Jsonschema is empty.")
        self.jsm_validator.validate(jsondata)
