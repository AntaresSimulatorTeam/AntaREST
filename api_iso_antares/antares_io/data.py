from pathlib import Path


from api_iso_antares.antares_io.ini import IniReader
from api_iso_antares.custom_types import JSON


class StudyReader:

    def __init__(self, reader_ini: IniReader):
        self._reader_ini = reader_ini

    def read(self, path: Path) -> JSON:
        study: JSON = {}
        study['settings'] = {}
        study['settings']['generaldata.ini'] = self._reader_ini.read_ini(path / "settings/generaldata.ini")
        print('JSON DATA', study)
        return study


