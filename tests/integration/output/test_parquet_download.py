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
import io
from pathlib import Path

from starlette.testclient import TestClient

from antarest.core.utils.archives import archive_dir
from antarest.output.filestudy.download import build_matrix_aggregation_result
from antarest.output.filestudy.variables import extract_variables_list
from antarest.output.model import StudyDownloadDTO, StudyDownloadType
from antarest.study.model import MatrixFrequency
from tests.test_helpers.parquet_outputs import rich_output


def test_import_and_download_parquet(admin_client: TestClient, tmp_path: Path):
    source = rich_output(tmp_path / "20260810-1420eco-contract")
    archive = tmp_path / "output.zip"
    archive_dir(source, archive)
    response = admin_client.post("/v1/studies", params={"name": "Parquet download contract"})
    assert response.status_code == 201, response.text
    study_id = response.json()
    response = admin_client.post(
        f"/v1/studies/{study_id}/output?storage_type=V2", files={"output": io.BytesIO(archive.read_bytes())}
    )
    assert response.status_code == 202, response.text
    output_id = response.json()
    for kind, clusters in [
        (StudyDownloadType.AREA, True),
        (StudyDownloadType.DISTRICT, True),
        (StudyDownloadType.LINK, False),
    ]:
        for frequency in MatrixFrequency:
            selection = StudyDownloadDTO(type=kind, level=frequency, years=[1], include_clusters=clusters)
            response = admin_client.post(
                f"/v1/studies/{study_id}/outputs/{output_id}/download",
                json=selection.model_dump(mode="json", by_alias=True),
            )
            assert response.status_code == 200, response.text
            expected = build_matrix_aggregation_result(source, selection)
            assert response.json() == expected.model_dump(mode="json")
    response = admin_client.get(f"/v1/studies/{study_id}/output/{output_id}/variables-list")
    assert response.status_code == 200, response.text
    assert response.json() == extract_variables_list(source).model_dump(mode="json", by_alias=True)
