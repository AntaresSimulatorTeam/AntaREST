from typing import Any, Optional
from uuid import UUID

from flask import Blueprint, jsonify, request

from antarest.launcher.service import LauncherService


def create_launcher_api(service: LauncherService) -> Blueprint:
    bp = Blueprint(
        "create_launcher_api",
        __name__,
    )

    @bp.route("/launcher/run/<string:study_id>", methods=["POST"])
    def run(study_id: str) -> Any:
        return jsonify({"job_id": service.run_study(study_id)})

    @bp.route("/launcher/jobs", methods=["GET"])
    def get_job() -> Any:
        study_id: Optional[str] = None
        if "study" in request.args:
            study_id = request.args["study"]

        return jsonify(
            {"jobs": [job.to_dict() for job in service.get_jobs(study_id)]}
        )

    @bp.route("/launcher/jobs/<uuid:job_id>", methods=["GET"])
    def get_result(job_id: UUID) -> Any:
        return jsonify(service.get_result(job_id).to_dict())

    return bp
