# Copyright (c) 2026, RTE (https://www.rte-france.com)
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


from sqlalchemy import select

from antarest.core.filetransfer.model import FileDownload
from antarest.core.utils.fastapi_sqlalchemy import db


class FileDownloadRepository:
    def add(self, download: FileDownload) -> None:
        db.session.add(download)
        db.session.commit()

    def get(self, download_id: str) -> FileDownload | None:
        download = db.session.get(FileDownload, download_id)
        db.session.refresh(download)
        return download

    def save(self, download: FileDownload) -> None:
        db.session.merge(download)
        db.session.add(download)
        db.session.commit()

    def get_all(self, owner: int | None = None) -> list[FileDownload]:
        stmt = select(FileDownload)
        if owner:
            stmt = stmt.where(FileDownload.owner == owner)

        result = db.session.execute(stmt)
        return list(result.scalars().all())

    def delete(self, download_id: str) -> None:
        download = self.get(download_id)
        if download:
            db.session.delete(download)
            db.session.commit()
