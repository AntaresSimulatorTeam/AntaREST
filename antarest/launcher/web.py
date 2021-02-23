from typing import Any
from uuid import UUID

from flask import Blueprint, jsonify

from antarest.launcher.service import LauncherService


def create_launcher_api(service: LauncherService) -> Blueprint:
    bp = Blueprint(
        "create_launcher_api",
        __name__,
    )

    @bp.route("/studies/<string:study_id>/run", methods=["POST"])
    def run(study_id: str) -> Any:
        return jsonify({"job_id": service.run_study(study_id)})

    @bp.route("/jobs/<uuid:job_id>", methods=["GET"])
    def get_result(job_id: UUID) -> Any:
        return jsonify(service.get_result(job_id).to_dict())

    return bp
