from pathlib import Path
from typing import Optional

from flask import Flask
from flask_jwt_extended import JWTManager  # type: ignore

from antarest.common.config import Config
from antarest.login.repository import UserRepository
from antarest.login.service import LoginService
from antarest.login.web import create_login_api


def build_login(
    application: Flask, config: Config, service: Optional[LoginService] = None
) -> None:
    if service is None:
        repo = UserRepository(config)
        service = LoginService(user_repo=repo)
    jwt = JWTManager(application)
    application.register_blueprint(create_login_api(service, config))
