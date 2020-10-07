import json
from pathlib import Path
from typing import Any

from jsonschema import validate  # type: ignore

from api_iso_antares.antares_io.reader.study_reader import StudyReader
from api_iso_antares.engine.url_engine import UrlEngine


class App:
    def __init__(self, simulation_reader: StudyReader, url_engine: UrlEngine):
        self.simulation_reader = simulation_reader
        self.url_engine = url_engine

    def get(self, route: str) -> Any:
        project_dir: Path = Path(__file__).resolve().parents[0]
        path_to_ini = project_dir / "../tests/integration/study"
        data = self.simulation_reader.read(path_to_ini)

        jsonschema = json.load((project_dir / "jsonschema.json").open())

        validate(data, jsonschema)

        return self.url_engine.apply(route, jsonschema, data)
