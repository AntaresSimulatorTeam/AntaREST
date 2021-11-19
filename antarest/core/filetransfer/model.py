import uuid
from http import HTTPStatus
from http.client import HTTPException

from pydantic import BaseModel
from sqlalchemy import Column, String, Integer, DateTime, Boolean

from antarest.core.persistence import Base


class FileDownloadNotFound(HTTPException):
    def __init__(self):
        super().__init__(
            HTTPStatus.NOT_FOUND,
            f"Requested download file was not found. It must have expired",
        )


class FileDownloadNotReady(HTTPException):
    def __init__(self):
        super().__init__(
            HTTPStatus.NOT_ACCEPTABLE,
            f"Requested file is not ready for download.",
        )


class FileDownloadDTO(BaseModel):
    id: str
    name: str
    filename: str
    expiration_date: str
    ready: bool


class FileDownload(Base):
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
    ready = Column(Boolean, server_default=False)
    expiration_date = Column(DateTime)

    def to_dto(self):
        return FileDownloadDTO(
            id=self.id,
            name=self.name,
            filename=self.filename,
            ready=self.ready,
            expiration_date=self.expiration_date,
        )
