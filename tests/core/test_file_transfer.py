import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi import FastAPI, Depends
from sqlalchemy import create_engine
from starlette.testclient import TestClient

from antarest.core.config import Config, StorageConfig
from antarest.core.filetransfer.repository import FileDownloadRepository
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.interfaces.eventbus import EventType, Event
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.model import PermissionInfo, PublicMode
from antarest.core.requests import RequestParameters, MustBeAuthenticatedError
from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware, db
from antarest.dbmodel import Base


def create_app() -> FastAPI:
    app = FastAPI(title=__name__)
    return app


def test_file_request():
    app = create_app()
    ftm = FileTransferManager(Mock(), Mock(), Config())

    @app.get("/dummy")
    def dummy_endpoint(tmppath: Path = Depends(ftm.request_tmp_file)):
        tmppath.touch()
        assert tmppath.exists()
        return tmppath

    client = TestClient(app, raise_server_exceptions=False)
    res = client.get("/dummy")
    tmppath = res.json()
    assert tmppath is not None
    assert not Path(tmppath).exists()


def test_lifecycle(tmp_path: Path):
    engine = create_engine("sqlite:///:memory:", echo=True)
    Base.metadata.create_all(engine)
    DBSessionMiddleware(
        Mock(),
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )

    with db():
        event_bus = Mock()
        ftm = FileTransferManager(
            FileDownloadRepository(),
            event_bus,
            Config(storage=StorageConfig(tmp_dir=tmp_path)),
        )
        with pytest.raises(MustBeAuthenticatedError):
            ftm.list_downloads(params=RequestParameters())

        downloads = ftm.list_downloads(
            params=RequestParameters(user=DEFAULT_ADMIN_USER)
        )
        assert len(downloads) == 0

        # creation
        filedownload = ftm.request_download(
            "some file", "some name", DEFAULT_ADMIN_USER
        )
        downloads = ftm.list_downloads(
            params=RequestParameters(user=DEFAULT_ADMIN_USER)
        )
        assert len(downloads) == 1

        # fail and remove
        ftm.fail(filedownload.id)
        event_bus.push.assert_called_with(
            Event(
                type=EventType.DOWNLOAD_FAILED,
                payload=filedownload.to_dto(),
                permissions=PermissionInfo(
                    owner=1, groups=[], public_mode=PublicMode.NONE
                ),
                channel="",
            )
        )
        filedownload_id = filedownload.id
        ftm.remove(filedownload.id)
        event_bus.push.assert_called_with(
            Event(
                type=EventType.DOWNLOAD_EXPIRED,
                payload=filedownload_id,
                permissions=PermissionInfo(
                    owner=1, groups=[], public_mode=PublicMode.NONE
                ),
                channel="",
            )
        )

        # expiration
        filedownload = ftm.request_download(
            "some file", "some name", DEFAULT_ADMIN_USER
        )
        downloads = ftm.list_downloads(
            params=RequestParameters(user=DEFAULT_ADMIN_USER)
        )
        assert len(downloads) == 1
        filedownload.expiration_date = datetime.datetime.now(
            datetime.timezone.utc
        ) - datetime.timedelta(seconds=5)
        ftm.repository.save(filedownload)
        downloads = ftm.list_downloads(
            params=RequestParameters(user=DEFAULT_ADMIN_USER)
        )
        assert len(downloads) == 0
