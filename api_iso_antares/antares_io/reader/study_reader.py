import os
from glob import glob
from pathlib import Path
from typing import Tuple, List

from api_iso_antares.antares_io.reader import IniReader
from api_iso_antares.custom_types import JSON, SUB_JSON
from jsonschema import validate


class StudyReader:
    def __init__(self, reader_ini: IniReader, jsonschema: JSON):
        self._reader_ini = reader_ini
        self.jsonschema = jsonschema

    def read(self, study_path: Path, do_validate: bool = True) -> JSON:
        study: JSON = dict()
        sub_study: JSON = study
        previous_parts: Tuple[str, ...] = tuple()

        for path in glob(f"{study_path}/**", recursive=True)[1:]:

            relative_path_str = path.replace(str(study_path) + os.sep, "")
            relative_path = Path(relative_path_str)
            parts = relative_path.parts[:-1]

            if relative_path.suffix:
                if previous_parts != parts:
                    sub_study = StudyReader._handle_folder(parts, study)
                sub_study[relative_path.name] = self._handle_file(
                    path, study_path
                )
                previous_parts = parts

        if do_validate:
            self.validate(study)

        return study

    def _handle_file(self, path: str, study_path: Path) -> SUB_JSON:
        path_file = Path(path)
        ext = path_file.suffix
        if ext == ".ini":
            return self._reader_ini.read(path_file)
        elif ext == ".txt":
            study_path_parent = str(study_path.parent) + os.sep
            relative_path = path.replace(study_path_parent, "")
            return f"matrices{os.sep}{relative_path}"
        return path

    @staticmethod
    def _handle_folder(parts: Tuple[str, ...], study: JSON) -> JSON:
        for part in parts:
            if part not in study:
                study[part] = {}
            study = study[part]
        return study

    def validate(self, study_json: JSON) -> None:
        if (not self.jsonschema) and study_json:
            raise ValueError("Jsonschema is empty.")
        validate(study_json, self.jsonschema)
