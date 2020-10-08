from typing import Any

from flask import Flask, jsonify

from api_iso_antares.custom_exceptions import HtmlException
from api_iso_antares.web.request_handler import RequestHandler

request_handler: RequestHandler


def create_routes(application: Flask) -> None:
    @application.route(
        "/api/studies/<path:path>",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    )
    def studies(path: str) -> Any:
        global request_handler
        try:
            output = request_handler.get(path)
        except HtmlException as e:
            return e.message, e.html_code_error
        return jsonify(output), 200


def create_server(req: RequestHandler) -> Flask:
    global request_handler
    request_handler = req
    application = Flask(__name__)
    create_routes(application)
    return application
