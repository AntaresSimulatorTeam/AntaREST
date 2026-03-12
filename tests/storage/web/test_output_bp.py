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
from http import HTTPStatus
from pathlib import Path
from unittest.mock import Mock

from antarest.core.config import Config, StorageConfig
from antarest.core.filetransfer.model import FileDownloadDTO, FileDownloadTaskDTO
from antarest.output.service import OutputService
from tests.storage.conftest import SimpleFileTransferManager
from tests.storage.integration.conftest import UUID
from tests.storage.web.test_studies_bp import create_test_client


def test_output_whole_download(tmp_path: Path) -> None:
    output_id = "my_output_id"

    expected = FileDownloadTaskDTO(
        file=FileDownloadDTO(
            id="some id",
            name="name",
            filename="filename",
            expiration_date=None,
            ready=True,
        ),
        task="some-task",
    )

    ftm = SimpleFileTransferManager(Config(storage=StorageConfig(tmp_dir=tmp_path)))
    output_service = Mock(spec=OutputService)
    output_service._study_service = Mock()
    output_service.export_output.return_value = expected
    output_service._file_transfer_manager = ftm
    client = create_test_client(Mock(), output_service, ftm, raise_server_exceptions=False)
    res = client.get(
        f"/v1/studies/{UUID}/outputs/{output_id}/export",
    )
    assert res.status_code == HTTPStatus.OK
