from typing import Optional

from flask import Flask
from flask_jwt_extended import JWTManager  # type: ignore

from antarest.login.repository import UserRepository
from antarest.login.service import LoginService
from antarest.login.web import create_login_api


def build_login(
    application: Flask, service: Optional[LoginService] = None
) -> None:
    repo = UserRepository()
    service = service or LoginService(user_repo=repo)
    jwt = JWTManager(application)
    application.register_blueprint(create_login_api(service))
