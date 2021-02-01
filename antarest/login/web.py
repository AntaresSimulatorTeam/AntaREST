import json
from typing import Any, Optional

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (  # type: ignore
    create_access_token,
    jwt_required,
    get_jwt_identity,
)

from antarest.login.model import User
from antarest.login.service import LoginService


def create_login_api(service: LoginService) -> Blueprint:
    bp = Blueprint("create_login_api", __name__)

    @bp.route("/auth", methods=["POST"])
    def auth() -> Any:
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
        access_token = create_access_token(identity=user.to_dict())
        return jsonify(access_token=access_token), 200

    @bp.route("/users", methods=["GET", "POST"], defaults={"id": None})
    @bp.route("/users/<int:id>", methods=["DELETE"])
    @jwt_required  # type: ignore
    def users(id: Optional[int]) -> Any:
        if get_jwt_identity()["role"] != "ADMIN":
            return "Only admin can manage user", 403

        if request.method == "GET":
            return jsonify([u.to_dict() for u in service.get_all()])

        if request.method == "POST":
            user = User.from_dict(json.loads(request.data))
            return jsonify(service.save(user).to_dict())

        if id is not None and request.method == "DELETE":
            service.delete(id)
            return jsonify(id), 200

    @bp.route("/protected")
    @jwt_required  # type: ignore
    def protected() -> Any:
        return f"user id={get_jwt_identity()}"

    return bp
