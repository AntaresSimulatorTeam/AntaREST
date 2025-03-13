# Copyright (c) 2025, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import uuid
from http import HTTPStatus
from http.client import HTTPException
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import mapped_column
from typing_extensions import override

from antarest.core.persistence import Base
from antarest.core.serde import AntaresBaseModel


class FileDownloadNotFound(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            HTTPStatus.NOT_FOUND,
            "Requested download file was not found. It must have expired",
        )


class FileDownloadNotReady(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            HTTPStatus.NOT_ACCEPTABLE,
            "Requested file is not ready for download.",
        )


class FileDownloadDTO(AntaresBaseModel):
    id: str
    name: str
    filename: str
    expiration_date: Optional[str] = None
    ready: bool
    failed: bool = False
    error_message: str = ""


class FileDownloadTaskDTO(AntaresBaseModel):
    file: FileDownloadDTO
    task: str


class FileDownload(Base):
    __tablename__ = "file_download"

    id = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
    )
    owner = mapped_column(Integer)
    name = mapped_column(String)
    filename = mapped_column(String)
    path = mapped_column(String)
    ready = mapped_column(Boolean, default=False)
    expiration_date = mapped_column(DateTime)
    failed = mapped_column(Boolean, default=False)
    error_message = mapped_column(String)

    def to_dto(self) -> FileDownloadDTO:
        return FileDownloadDTO(
            id=self.id,
            name=self.name,
            filename=self.filename,
            ready=self.ready,
            expiration_date=str(self.expiration_date) if self.expiration_date is not None else None,
            failed=self.failed or False,
            error_message=self.error_message or "",
        )

    @override
    def __repr__(self) -> str:
        return (
            f"(id={self.id},"
            f" name={self.name},"
            f" filename={self.filename},"
            f" path={self.path},"
            f" ready={self.ready},"
            f" expiration_date={self.expiration_date})"
        )
