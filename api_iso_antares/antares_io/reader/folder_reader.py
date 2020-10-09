import os
from glob import glob
from pathlib import Path
from typing import Tuple

from jsonschema import validate

from api_iso_antares.antares_io.reader.ini_reader import IniReader
from api_iso_antares.custom_types import JSON, SUB_JSON


class FolderReader:
    def __init__(self, reader_ini: IniReader, jsonschema: JSON):
        self._reader_ini = reader_ini
        self.jsonschema = jsonschema

    def read(self, folder_path: Path, do_validate: bool = True) -> JSON:
        folder: JSON = dict()
        sub_folder: JSON = folder
        previous_parts: Tuple[str, ...] = tuple()

        for path in glob(f"{folder_path}/**", recursive=True)[1:]:

            relative_path_str = path.replace(str(folder_path) + os.sep, "")
            relative_path = Path(relative_path_str)
            parts = relative_path.parts[:-1]

            if relative_path.suffix:
                if previous_parts != parts:
                    sub_folder = FolderReader._handle_folder(parts, folder)
                sub_folder[relative_path.name] = self._handle_file(
                    path, folder_path
                )
                previous_parts = parts

        if do_validate:
            self.validate(folder)

        return folder

    def _handle_file(self, path: str, folder_path: Path) -> SUB_JSON:
        path_file = Path(path)
        ext = path_file.suffix
        if ext == ".ini":
            return self._reader_ini.read(path_file)
        elif ext == ".txt":
            folder_path_parent = str(folder_path.parent) + os.sep
            relative_path = path.replace(folder_path_parent, "")
            return f"matrices{os.sep}{relative_path}"
        return path

    @staticmethod
    def _handle_folder(parts: Tuple[str, ...], folder: JSON) -> JSON:
        for part in parts:
            if part not in folder:
                folder[part] = {}
            folder = folder[part]
        return folder

    def validate(self, folder_json: JSON) -> None:
        if (not self.jsonschema) and folder_json:
            raise ValueError("Jsonschema is empty.")
        validate(folder_json, self.jsonschema)
