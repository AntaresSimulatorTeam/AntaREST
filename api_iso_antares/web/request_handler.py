import json
from pathlib import Path
from typing import Any

from jsonschema import validate  # type: ignore

from api_iso_antares.antares_io.reader import StudyReader
from api_iso_antares.engine import UrlEngine


class RequestHandler:
    def __init__(
        self,
        study_reader: StudyReader,
        url_engine: UrlEngine,
        path_to_schema: Path,
        path_to_study: Path,
    ):
        self.study_reader = study_reader
        self.url_engine = url_engine
        self.path_to_schema = path_to_schema
        self.path_to_study = path_to_study

    def get(self, route: str) -> Any:
        data = self.study_reader.read(self.path_to_study)

        jsonschema = json.load(self.path_to_schema.open())

        validate(data, jsonschema)

        return self.url_engine.apply(route, jsonschema, data)
