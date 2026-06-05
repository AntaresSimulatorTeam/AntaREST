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

import datetime
import time
from pathlib import Path
from threading import Thread
from unittest.mock import Mock

import pytest
from fastapi import Depends, FastAPI
from starlette.testclient import TestClient

from antarest.core.config import Config, StorageConfig
from antarest.core.filetransfer.repository import FileDownloadRepository
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.interfaces.eventbus import Event, EventType
from antarest.core.model import PermissionInfo, PublicMode
from antarest.core.requests import MustBeAuthenticatedError
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.fastapi_sqlalchemy.middleware import get_session_factory
from antarest.login.utils import current_user_context
from tests.helpers import with_admin_user
from tests.test_helpers.db import create_db_event_counter


def test_file_request() -> None:
    app = FastAPI(title=__name__)
    ftm = FileTransferManager(Mock(), Mock(), Config())

    @app.get("/dummy")
    def dummy_endpoint(tmppath: Path = Depends(ftm.request_tmp_file)) -> Path:
        tmppath.touch()
        assert tmppath.exists()
        return tmppath

    client = TestClient(app, raise_server_exceptions=False)
    res = client.get("/dummy")
    tmppath = res.json()
    assert tmppath is not None
    assert not Path(tmppath).exists()


@with_admin_user
def test_lifecycle(tmp_path: Path) -> None:
    with db():
        event_bus = Mock()
        ftm = FileTransferManager(
            FileDownloadRepository(),
            event_bus,
            Config(storage=StorageConfig(tmp_dir=tmp_path)),
        )
        with pytest.raises(MustBeAuthenticatedError):
            with current_user_context(None):
                ftm.list_downloads()

        downloads = ftm.list_downloads()
        assert len(downloads) == 0

        # creation
        filedownload = ftm.request_download("some file", "some name")
        downloads = ftm.list_downloads()
        assert len(downloads) == 1

        # fail
        ftm.fail(filedownload.id)
        event_bus.push.assert_called_with(
            Event(
                type=EventType.DOWNLOAD_FAILED,
                payload=filedownload.to_dto(),
                permissions=PermissionInfo(owner=1, groups=[], public_mode=PublicMode.NONE),
                channel="",
            )
        )

        # expiration
        downloads = ftm.list_downloads()
        assert len(downloads) == 1
        filedownload.expiration_date = datetime.datetime.now(datetime.UTC) - datetime.timedelta(seconds=5)
        ftm.repository.save(filedownload)
        downloads = ftm.list_downloads()
        assert len(downloads) == 0


@with_admin_user
def test_wait_for_download_metadata(tmp_path: Path) -> None:
    with db():
        ftm = FileTransferManager(
            repository=FileDownloadRepository(),
            event_bus=Mock(),
            config=Config(storage=StorageConfig(tmp_dir=tmp_path)),
        )
        download = ftm.request_download("some file", "some name")
        assert download.id is not None

        def set_ready_after_1s() -> None:
            time.sleep(1)
            with db():
                ftm.set_ready(download.id)

        thread = Thread(target=set_ready_after_1s)
        thread.start()

        events_counter = create_db_event_counter(get_session_factory())
        download_dto = ftm.get_download_metadata(
            download.id, wait_for_availability=True, polling_interval=0.1, timeout=10
        )

        assert download_dto.id == download.id
        assert download_dto.ready

        # We check there's been only 1 commit (set ready)
        # and that the polling used short transactions (begin/rollback each time)
        assert events_counter.commit == 1
        assert events_counter.begin >= 8
        assert events_counter.rollback >= 8

        thread.join()
