from typing import Any

from flask import Flask

from api_iso_antares.engine.url import UrlEngine

application = Flask(__name__)

engine = UrlEngine({}, {})


@application.route(
    "/api/<path:path>", methods=["GET", "POST", "PUT", "PATCH", "DELETE"]
)
def home(path: str) -> Any:
    output = engine.apply(path)
    if output is None:
        return "", 404
    return output


if __name__ == "__main__":
    application.run(debug=False, host="0.0.0.0", port=8080)
