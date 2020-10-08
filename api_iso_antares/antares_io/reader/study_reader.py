from glob import glob
from pathlib import Path
from typing import Tuple, List

from api_iso_antares.antares_io.reader import IniReader
from api_iso_antares.custom_types import JSON, SUB_JSON


class StudyReader:
    def __init__(self, reader_ini: IniReader):
        self._reader_ini = reader_ini

    def read(self, study_path: Path) -> JSON:
        study: JSON = dict()
        sub_study: JSON = dict()
        previous_parts: Tuple[str, ...] = tuple()

        for path in glob(f"{study_path}/**", recursive=True)[1:]:

            relative_path_str = path.replace(str(study_path) + "/", "")
            relative_path = Path(relative_path_str)
            parts = relative_path.parts[:-1]

            if relative_path.suffix:
                if previous_parts != parts:
                    sub_study = StudyReader._handle_folder(parts, study)
                sub_study[relative_path.name] = self._handle_file(
                    path, study_path
                )
                previous_parts = parts

        return study

    def _handle_file(self, path: str, study_path: Path) -> SUB_JSON:
        path_file = Path(path)
        ext = path_file.suffix
        if ext == ".ini":
            return self._reader_ini.read(path_file)
        elif ext == ".txt":
            study_path_parent = str(study_path.parent) + "/"
            relative_path = path.replace(study_path_parent, "")
            return f"matrices/{relative_path}"
        return path

    @staticmethod
    def _handle_folder(parts: Tuple[str, ...], study: JSON) -> JSON:
        for part in parts:
            if part not in study:
                study[part] = {}
            study = study[part]
        return study
