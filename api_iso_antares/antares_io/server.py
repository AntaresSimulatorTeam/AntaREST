import json
import os
from pathlib import Path
from typing import Any

from flask import Flask
from jsonschema import validate

from api_iso_antares.antares_io.ini import read_ini
from api_iso_antares.engine.url import UrlEngine

application = Flask(__name__)

project_dir: Path = Path(__file__).resolve().parents[1]
path_to_ini = project_dir / "../tests/integration/generaldata.ini"
data = read_ini(path_to_ini)

print(os.getcwd())
jsonschema = json.load(open("../../api_iso_antares/jsonschema.json"))

validate(data, jsonschema)

engine = UrlEngine(jsonschema, data)


@application.route(
    "/api/<path:path>", methods=["GET", "POST", "PUT", "PATCH", "DELETE"]
)
def home(path: str) -> Any:
    output = engine.apply(path)
    if output is None:
        return "", 404
    return json.dumps(output), 200


if __name__ == "__main__":
    application.run(debug=False, host="0.0.0.0", port=8080)
