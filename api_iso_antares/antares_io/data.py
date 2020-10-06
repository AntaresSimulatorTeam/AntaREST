from pathlib import Path
from typing import Any, Dict

from jsonschema import validate  # type: ignore

from antares_io.ini import IniReader
from custom_types import JSON


class SimulationReader:

    def __init__(self, reader_ini: IniReader):
        self._reader_ini = reader_ini

    def read_simulation(self, path: Path) -> JSON:
        simulation: JSON = {}
        simulation['settings'] = {}
        simulation['settings']['generaldata.ini'] = self._reader_ini.read_ini(path / "settings/generaldata.ini")
        print('JSON DATA', simulation)
        return simulation


