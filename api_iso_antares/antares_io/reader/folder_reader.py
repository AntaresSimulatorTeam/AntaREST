import os
from copy import deepcopy
from pathlib import Path

from jsonschema import validate

from api_iso_antares.antares_io.reader.ini_reader import IniReader
from api_iso_antares.antares_io.reader.offset import Offset
from api_iso_antares.custom_exceptions import HtmlException
from api_iso_antares.custom_types import JSON, SUB_JSON


class PathNotMatchJsonSchema(HtmlException):
    def __init__(self, message: str) -> None:
        super(PathNotMatchJsonSchema, self).__init__(message, 405)


class FolderReader:
    def __init__(self, reader_ini: IniReader, jsonschema: JSON, root: Path):
        self._reader_ini = reader_ini
        self.jsonschema = jsonschema
        self.root = root

    def read(self, folder: Path) -> JSON:
        jsonschema = deepcopy(self.jsonschema)
        output: JSON = dict()
        offset = Offset(path=folder, json_data=output, jsm=jsonschema)
        # self._parse_recursive(folder, jsonschema, output)
        self._parse_recursive(offset)
        return output

    def _parse_recursive(self, offset: Offset) -> None:

        # keys = jsonschema["properties"].items()
        keys = offset.get_properties()
        for key, value in keys:
            # child_path = current_path / key
            child = offset.next(key)
            if not child.path.exists():
                raise PathNotMatchJsonSchema(
                    f"{child.path} not in study. Needs keys {keys}"
                )

            # child_jsonschema = jsonschema["properties"][key]

            if child.path.is_dir():
                self._parse_dir(child.path, child.jsm, offset.output, key)
            else:
                offset.set_data(key, self._parse_file(child.path))

    def _parse_dir(self, child: Offset, parent: Offset, key: str) -> None:
        # jsm_type = jsonschema["type"]
        jsm_type = child.jsm["type"]
        if jsm_type == "object":
            parent.json_data[key] = {}
            child.json_data = parent.json_data
            self._parse_recursive(child)
        elif jsm_type == "array":
            # output[key] = []
            parent.json_data[key] = []
            # del jsonschema["items"]["properties"]["name"]

            sorted_areas = sorted(child.path.iterdir())
            for path in sorted_areas:
                parent.json_data[key].append({"name": path.name})
                child.json_data = parent.json_data
                self._parse_recursive(
                    # path, jsonschema["items"], output[key][-1]
                    child
                )

    def _parse_file(self, path: Path) -> SUB_JSON:
        if path.suffix == ".txt":
            path_parent = f"{self.root}{os.sep}"
            relative_path = str(path).replace(path_parent, "")
            return f"matrices{os.sep}{relative_path}"
        elif path.suffix == ".ini":
            return self._reader_ini.read(path)
        raise NotImplemented(
            f"File extension {path.suffix} not implemented"
        )  # TODO custom exception

    def validate(self, json_data: JSON) -> None:
        if (not self.jsonschema) and json_data:
            raise ValueError("Jsonschema is empty.")
        validate(json_data, self.jsonschema)
