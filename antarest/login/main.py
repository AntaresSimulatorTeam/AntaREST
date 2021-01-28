from flask import Flask

from antarest.login.repository import UserRepository
from antarest.login.service import LoginService
from antarest.login.web import create_login_api


def build_login(application: Flask):
    repo = UserRepository()
    service = LoginService(user_repo=repo)

    application.register_blueprint(create_login_api(service))
