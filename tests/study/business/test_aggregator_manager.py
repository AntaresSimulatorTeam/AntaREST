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

import zipfile
from pathlib import Path

import pytest

from antarest.core.exceptions import FileTooLargeError
from antarest.study.business.aggregator_management import AggregatorManager, MCIndAreasQueryFile
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency


@pytest.fixture(name="get_output_path")
def get_output_path_fixture(tmp_path: Path, project_path: Path) -> Path:
    # Prepare the directories used by the repos
    zipped_study_path = project_path.joinpath("examples/studies/STA-mini.zip")

    # Extract the sample study
    with zipfile.ZipFile(zipped_study_path) as zip_output:
        zip_output.extractall(path=tmp_path)

    return tmp_path.joinpath("STA-mini/output")


@pytest.mark.integration
def test_storage_different_max_size_value(get_output_path: Path):
    """
    SetUp: This test unzip the STA-mini study that contains outputs.
    Initialize an aggregator manager first with a high value and next change it for a low value.

    Test: The first call on aggregate_output_data should pass
    and the second should fail.

    For this test we use the `20201014-1425eco-goodbye` outputs because it has enough data
    to check the estimated size of df.
    """
    output_path = get_output_path.joinpath("20201014-1425eco-goodbye")

    # aggregation_results_max_size equals to 200Mo
    aggregator_manager = AggregatorManager(
        output_path=output_path,
        query_file=MCIndAreasQueryFile.DETAILS,
        frequency=MatrixFrequency.HOURLY,
        ids_to_consider=[],
        columns_names=[],
        aggregation_results_max_size=200,
    )

    # must pass
    res = aggregator_manager.aggregate_output_data()
    assert res.empty is False

    aggregator_manager.aggregation_results_max_size = 0

    # must fail
    with pytest.raises(FileTooLargeError):
        aggregator_manager.aggregate_output_data()
