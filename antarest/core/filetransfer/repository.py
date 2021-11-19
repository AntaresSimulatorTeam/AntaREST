from typing import Optional, List

from antarest.core.filetransfer.model import FileDownload
from antarest.core.utils.fastapi_sqlalchemy import db


class FileDownloadRepository:
    def add(self, download: FileDownload):
        db.session.add(download)
        db.session.commit()

    def get(self, download_id: str) -> Optional[FileDownload]:
        return db.session.query(FileDownload).get(download_id)

    def save(self, download: FileDownload):
        db.session.merge(download)
        db.session.add(download)
        db.session.commit()

    def get_all(self, owner: Optional[int] = None) -> List[FileDownload]:
        if owner:
            return (
                db.session.query(FileDownload)
                .filter(FileDownload.owner == owner)
                .fetch_all()
            )
        return db.session.query(FileDownload).all()
