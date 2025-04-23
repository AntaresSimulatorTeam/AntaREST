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

import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi import Depends, FastAPI
from sqlalchemy import create_engine
from starlette.testclient import TestClient

from antarest.core.config import Config, StorageConfig
from antarest.core.filetransfer.repository import FileDownloadRepository
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.interfaces.eventbus import Event, EventType
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.model import PermissionInfo, PublicMode
from antarest.core.requests import MustBeAuthenticatedError
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
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    # noinspection SpellCheckingInspection
    DBSessionMiddleware(
        None,
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
            ftm.list_downloads()

        downloads = ftm.list_downloads()
        assert len(downloads) == 0

        # creation
        filedownload = ftm.request_download("some file", "some name", DEFAULT_ADMIN_USER)
        downloads = ftm.list_downloads()
        assert len(downloads) == 1

        # fail and remove
        ftm.fail(filedownload.id)
        event_bus.push.assert_called_with(
            Event(
                type=EventType.DOWNLOAD_FAILED,
                payload=filedownload.to_dto(),
                permissions=PermissionInfo(owner=1, groups=[], public_mode=PublicMode.NONE),
                channel="",
            )
        )
        filedownload_id = filedownload.id
        ftm.remove(filedownload.id)
        event_bus.push.assert_called_with(
            Event(
                type=EventType.DOWNLOAD_EXPIRED,
                payload=filedownload_id,
                permissions=PermissionInfo(owner=1, groups=[], public_mode=PublicMode.NONE),
                channel="",
            )
        )

        # expiration
        filedownload = ftm.request_download("some file", "some name", DEFAULT_ADMIN_USER)
        downloads = ftm.list_downloads()
        assert len(downloads) == 1
        filedownload.expiration_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=5)
        ftm.repository.save(filedownload)
        downloads = ftm.list_downloads()
        assert len(downloads) == 0
