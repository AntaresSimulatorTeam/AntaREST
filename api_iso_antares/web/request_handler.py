from pathlib import Path
from typing import Any

from api_iso_antares.antares_io.reader import StudyReader
from api_iso_antares.engine import UrlEngine


class RequestHandler:
    def __init__(
        self,
        study_reader: StudyReader,
        url_engine: UrlEngine,
        path_to_study: Path,
    ):
        self.study_reader = study_reader
        self.url_engine = url_engine
        self.path_to_study = path_to_study

    def get(self, route: str) -> Any:

        data = self.study_reader.read(self.path_to_study)
        self.study_reader.validate(data)

        return self.url_engine.apply(route, data)
