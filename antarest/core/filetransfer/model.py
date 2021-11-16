import uuid

from sqlalchemy import Column, String

from antarest.core.persistence import Base


class FileDownload(Base):
    __tablename__ = "file_download"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
    )
    name = Column(String)