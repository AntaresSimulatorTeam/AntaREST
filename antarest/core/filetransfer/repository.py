from typing import Optional, List

from antarest.core.filetransfer.model import FileDownload
from antarest.core.utils.fastapi_sqlalchemy import db


class FileDownloadRepository:
    def add(self, download: FileDownload) -> None:
        db.session.add(download)
        db.session.commit()

    def get(self, download_id: str) -> Optional[FileDownload]:
        file_download: Optional[FileDownload] = db.session.query(
            FileDownload
        ).get(download_id)
        return file_download

    def save(self, download: FileDownload) -> None:
        db.session.merge(download)
        db.session.add(download)
        db.session.commit()

    def get_all(self, owner: Optional[int] = None) -> List[FileDownload]:
        file_download_list: List[FileDownload] = []
        if owner:
            file_download_list = (
                db.session.query(FileDownload)
                .filter(FileDownload.owner == owner)
                .fetch_all()
            )
        else:
            file_download_list = db.session.query(FileDownload).all()
        return file_download_list

    def delete(self, download_id: str) -> None:
        download = self.get(download_id)
        if download:
            db.session.delete(download)
