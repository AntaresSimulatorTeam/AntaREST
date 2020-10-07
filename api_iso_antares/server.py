import json
from typing import Any

from flask import Flask

from api_iso_antares.antares_io.reader import IniReader, StudyReader
from api_iso_antares.engine import UrlEngine
from api_iso_antares.main import App

application = Flask(__name__)
app = App(
    simulation_reader=StudyReader(reader_ini=IniReader()),
    url_engine=UrlEngine(),
)


@application.route(
    "/api/simulations/<path:path>",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
def home(path: str) -> Any:
    output = app.get(path)
    if output is None:
        return "", 404
    return json.dumps(output), 200


if __name__ == "__main__":
    application.run(debug=False, host="0.0.0.0", port=8080)
