from typing import Any

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
)

from antarest.login.service import LoginService


def create_login_api(service: LoginService) -> Blueprint:
    bp = Blueprint("create_login_api", __name__)

    @bp.route("/auth", methods=["POST"])
    def auth():
        if not request.is_json:
            return jsonify({"msg": "Missing JSON in request"}), 400

        username = request.json.get("username", None)
        password = request.json.get("password", None)
        if not username:
            return jsonify({"msg": "Missing username parameter"}), 400
        if not password:
            return jsonify({"msg": "Missing password parameter"}), 400

        user = service.authenticate(username, password)
        if not user:
            return jsonify({"msg": "Bad username or password"}), 401

        # Identity can be any data that is json serializable
        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token), 200

    @bp.route("/protected")
    @jwt_required
    def protected():
        return f"user id={get_jwt_identity()}"

    return bp
