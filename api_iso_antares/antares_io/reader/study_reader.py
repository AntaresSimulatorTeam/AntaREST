from glob import glob
from pathlib import Path
from typing import Tuple

from api_iso_antares.antares_io.reader import IniReader
from api_iso_antares.custom_types import JSON


class StudyReader:
    def __init__(self, reader_ini: IniReader):
        self._reader_ini = reader_ini

    def read(self, study_path: Path) -> JSON:
        study: JSON = dict()
        sub_study: JSON = None
        previous_parts = []

        for path in glob(f"{study_path}/**", recursive=True)[1:]:

            relative_path = path.replace(str(study_path) + "/", "")
            relative_path = Path(relative_path)
            parts = relative_path.parts[:-1]

            if relative_path.suffix:
                if previous_parts != parts:
                    sub_study = StudyReader._handle_folder(parts, study)
                sub_study[relative_path.name] = StudyReader._handle_file(path)
                previous_parts = parts

        return study

    @staticmethod
    def _handle_file(path: str) -> JSON:
        path = Path(path)
        ext = path.suffix
        if ext == '.ini':
            pass # TODO read ini
        elif ext == '.txt':
            pass # TODO get url

    @staticmethod
    def _handle_folder(parts: Tuple[str], study: JSON) -> JSON:
        for part in parts:
            if part not in study:
                study[part] = {}
            study = study[part]
        return study
