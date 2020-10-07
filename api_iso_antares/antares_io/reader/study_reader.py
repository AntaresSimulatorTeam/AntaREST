from glob import glob
from pathlib import Path
from typing import Tuple

from api_iso_antares.antares_io.reader import IniReader
from api_iso_antares.custom_types import JSON


class StudyReader:
    def __init__(self, reader_ini: IniReader):
        self._reader_ini = reader_ini

    def read(self, study_path: Path) -> JSON:

        # study: JSON = dict()
        # study["settings"] = {}
        # study["settings"]["generaldata.ini"] = self._reader_ini.read(
        #     path / "settings/generaldata.ini"
        # )
        # print("JSON DATA", study)
        # return study

        study: JSON = dict()

        for path in glob(f"{study_path}/**", recursive=True)[1:]:

            print(path)
            relative_path = path.replace(str(study_path) + "/", "")
            relative_path = Path(relative_path)

            sub_study: JSON
            if relative_path.suffix:
                sub_study = StudyReader._handle_file()
            else:
                sub_study = StudyReader._handle_folder(relative_path.parts)
            study.update(sub_study)

        return study

    @staticmethod
    def _handle_file() -> JSON:
        return {}

    @staticmethod
    def _handle_folder(parts: Tuple[str]) -> JSON:
        sub_study: JSON = dict()
        for part in parts:
            sub_study[part] = {}
            sub_study = sub_study[part]
        return sub_study
