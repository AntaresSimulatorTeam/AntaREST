from flask import Blueprint

from antarest.login.service import LoginService


def create_login_api(service: LoginService) -> Blueprint:
    bp = Blueprint("create_login_api", __name__)
    return bp
