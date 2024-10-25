from http import HTTPStatus

from fastapi import HTTPException


class WorkspaceNotFound(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.BAD_REQUEST, message)
