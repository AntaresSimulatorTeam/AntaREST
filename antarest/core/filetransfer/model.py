import uuid
from http import HTTPStatus
from http.client import HTTPException
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import Column, String, Integer, DateTime, Boolean  # type: ignore

from antarest.core.persistence import Base


class FileDownloadNotFound(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            HTTPStatus.NOT_FOUND,
            f"Requested download file was not found. It must have expired",
        )


class FileDownloadNotReady(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            HTTPStatus.NOT_ACCEPTABLE,
            f"Requested file is not ready for download.",
        )


class FileDownloadDTO(BaseModel):
    id: str
    name: str
    filename: str
    expiration_date: Optional[str]
    ready: bool
    failed: bool = False
    error_message: str = ""


class FileDownloadTaskDTO(BaseModel):
    file: FileDownloadDTO
    task: str


class FileDownload(Base):  # type: ignore
    __tablename__ = "file_download"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
    )
    owner = Column(Integer)
    name = Column(String)
    filename = Column(String)
    path = Column(String)
    ready = Column(Boolean, default=False)
    expiration_date = Column(DateTime)
    failed = Column(Boolean, default=False)
    error_message = Column(String)

    def to_dto(self) -> FileDownloadDTO:
        return FileDownloadDTO(
            id=self.id,
            name=self.name,
            filename=self.filename,
            ready=self.ready,
            expiration_date=str(self.expiration_date),
            failed=self.failed,
            error_message=self.error_message or "",
        )

    def __repr__(self) -> str:
        return f"(id={self.id},name={self.name},filename={self.filename},path={self.path},ready={self.ready},expiration_date={self.expiration_date})"
