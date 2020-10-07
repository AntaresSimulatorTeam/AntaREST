import json
import os
from pathlib import Path
from typing import Any

from flask import Flask
from jsonschema import validate  # type: ignore

from api_iso_antares.antares_io.ini import IniReader
from api_iso_antares.antares_io.data import StudyReader
from api_iso_antares.engine.url import UrlEngine


class App:
    def __init__(self, simulation_reader: StudyReader, url_engine: UrlEngine):
        self.simulation_reader = simulation_reader
        self.url_engine = url_engine

    def get(self, route: str) -> Any:
        project_dir: Path = Path(__file__).resolve().parents[1]
        path_to_ini = project_dir / "../tests/integration/study"
        data = self.simulation_reader.read(path_to_ini)

        print(os.getcwd())
        jsonschema = json.load((project_dir / "jsonschema.json").open())

        validate(data, jsonschema)

        return self.url_engine.apply(route, jsonschema, data)


application = Flask(__name__)
app = App(simulation_reader=StudyReader(reader_ini=IniReader()), url_engine=UrlEngine())

@application.route(
    "/api/simulations/<path:path>", methods=["GET", "POST", "PUT", "PATCH", "DELETE"]
)
def home(path: str) -> Any:
    output = app.get(path)
    if output is None:
        return "", 404
    return json.dumps(output), 200


if __name__ == "__main__":
    application.run(debug=False, host="0.0.0.0", port=8080)
