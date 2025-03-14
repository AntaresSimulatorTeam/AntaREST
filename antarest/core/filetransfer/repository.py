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

from typing import List, Optional

from antarest.core.filetransfer.model import FileDownload
from antarest.core.utils.fastapi_sqlalchemy import db


class FileDownloadRepository:
    def add(self, download: FileDownload) -> None:
        db.session.add(download)
        db.session.commit()

    def get(self, download_id: str) -> Optional[FileDownload]:
        file_download: Optional[FileDownload] = db.session.query(FileDownload).get(download_id)
        return file_download

    def save(self, download: FileDownload) -> None:
        db.session.merge(download)
        db.session.add(download)
        db.session.commit()

    def get_all(self, owner: Optional[int] = None) -> List[FileDownload]:
        file_download_list: List[FileDownload] = []
        if owner:
            file_download_list = db.session.query(FileDownload).filter(FileDownload.owner == owner).all()
        else:
            file_download_list = db.session.query(FileDownload).all()
        return file_download_list

    def delete(self, download_id: str) -> None:
        download = self.get(download_id)
        if download:
            db.session.delete(download)
            db.session.commit()
