import os
from copy import deepcopy
from pathlib import Path

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
        ini_reader: IniReader,
        jsm: JSON,
        root: Path,
        jsm_validator: JsmValidator,
    ):
        self._reader_ini = ini_reader
        self.jsonschema = jsm
        self.root = root
        self.jsm_validator = jsm_validator

    def read(self, folder: Path) -> JSON:
        jsonschema = deepcopy(self.jsonschema)
        output: JSON = dict()

        data_cursor = DataCursor(output)
        jsm_cursor = JsmCursor(jsonschema)
        path_cursor = PathCursor(folder)
        self._parse_recursive(path_cursor, data_cursor, jsm_cursor)

        self.validate(output)

        return output

    def _parse_recursive(
        self,
        path_cursor: PathCursor,
        data_cursor: DataCursor,
        jsm_cursor: JsmCursor,
    ) -> None:

        for key in jsm_cursor.get_properties():

            next_jsm = jsm_cursor.next(key)
            next_path = self._build_next_path_cursor(
                path_cursor, next_jsm, key
            )
            next_data = data_cursor.next(key, next_jsm)

            if next_path.is_dir():
                self._parse_dir(next_path, next_data, next_jsm)
            else:
                data_cursor.set(key, self._parse_file(next_path))

    def _parse_dir(
        self, path: PathCursor, data: DataCursor, jsm: JsmCursor
    ) -> None:
        if jsm.is_object():
            self._parse_recursive(path, data, jsm)
        elif jsm.is_array():
            for path, key in path.next_items():
                self._parse_recursive(path, data.next_item(key), jsm)

    def _parse_file(self, cursor: PathCursor) -> SUB_JSON:
        path = cursor.path
        if path.suffix in [".txt", ".log"]:
            path_parent = f"{self.root}{os.sep}"
            relative_path = str(path).replace(path_parent, "")
            return f"file{os.sep}{relative_path}"
        elif path.suffix in [
            ".ini",
            ".antares",
        ]:  # TODO: add a hook remove business antares
            return self._reader_ini.read(path)
        raise NotImplementedError(
            f"File extension {path.suffix} not implemented"
        )

    def _build_next_path_cursor(
        self, path_cursor: PathCursor, next_jsm: JsmCursor, key: str
    ) -> PathCursor:
        file_or_dirname = next_jsm.get_filename()
        if file_or_dirname is None:
            file_or_dirname = key
        return path_cursor.next(file_or_dirname)

    def validate(self, jsondata: JSON) -> None:
        if (not self.jsonschema) and jsondata:
            raise ValueError("Jsonschema is empty.")
        self.jsm_validator.validate(jsondata)
