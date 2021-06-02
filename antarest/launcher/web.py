from typing import Any, Optional
from uuid import UUID

from flask import Blueprint, jsonify, request
from markupsafe import escape

from antarest.login.auth import Auth
from antarest.common.config import Config
from antarest.common.requests import RequestParameters
from antarest.launcher.service import LauncherService


def create_launcher_api(service: LauncherService, config: Config) -> Blueprint:
    bp = Blueprint(
        "create_launcher_api",
        __name__,
    )

    auth = Auth(config)

    @bp.route("/launcher/run/<string:study_id>", methods=["POST"])
    @auth.protected()
    def run(study_id: str) -> Any:
        """
        Run study
        ---
        responses:
          '200':
            content:
              application/json:
                schema:
                    $ref: '#/definitions/RunInfo'
            description: Successful operation
          '400':
            description: Invalid request
          '401':
            description: Unauthenticated User
          '403':
            description: Unauthorized
        parameters:
        - in: path
          name: study_id
          required: true
          description: study id
          schema:
            type: string
        definitions:
            - schema:
                id: RunInfo
                properties:
                  job_id:
                    type: string
        tags:
          - Run Studies
        """
        study_id = str(escape(study_id))
        params = RequestParameters(user=Auth.get_current_user())
        return jsonify({"job_id": service.run_study(study_id, params)})

    @bp.route("/launcher/jobs", methods=["GET"])
    @auth.protected()
    def get_job() -> Any:
        """
        Retrieve jobs
        ---
        responses:
          '200':
            content:
              application/json:
                schema:
                    type: array
                    items:
                        $ref: '#/definitions/LaunchJob'
            description: Successful operation
          '400':
            description: Invalid request
          '401':
            description: Unauthenticated User
          '403':
            description: Unauthorized
        parameters:
        - in: query
          name: study
          required: false
          description: study id
          schema:
            type: string
        definitions:
            - schema:
                id: LaunchJob
                properties:
                  id:
                    type: string
                  study_id:
                    type: string
                  job_status:
                    type: string
                  creation_date:
                    type: string
                  completion_date:
                    type: string
                  msg:
                    type: string
                  exit_code:
                    type: number
        tags:
          - Run Studies
        """
        study_id: Optional[str] = None
        if "study" in request.args:
            study_id = request.args["study"]

        return jsonify([job.to_dict() for job in service.get_jobs(study_id)])

    @bp.route("/launcher/jobs/<uuid:job_id>", methods=["GET"])
    @auth.protected()
    def get_result(job_id: UUID) -> Any:
        """
        Retrieve job info from job id
        ---
        responses:
          '200':
            content:
              application/json:
                schema:
                  $ref: '#/definitions/LaunchJob'
            description: Successful operation
          '400':
            description: Invalid request
          '401':
            description: Unauthenticated User
          '403':
            description: Unauthorized
        parameters:
        - in: path
          name: job_id
          required: true
          description: job id
          schema:
            type: string
        definitions:
            - schema:
                id: LaunchJob
                properties:
                  id:
                    type: string
                  study_id:
                    type: string
                  job_status:
                    type: string
                  creation_date:
                    type: string
                  completion_date:
                    type: string
                  msg:
                    type: string
                  exit_code:
                    type: number
        tags:
          - Run Studies
        """
        return jsonify(service.get_result(job_id).to_dict())

    return bp
