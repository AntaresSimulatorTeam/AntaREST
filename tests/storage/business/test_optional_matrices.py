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

import numpy as np
import pytest

from antarest.core.exceptions import ChildNotFoundError
from antarest.study.business.model.sts_model import STStorageCreation
from antarest.study.business.model.thermal_cluster_model import ThermalClusterCreation
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_cluster import CreateCluster
from antarest.study.storage.variantstudy.model.command.create_st_storage import CreateSTStorage
from antarest.study.storage.variantstudy.model.command_context import CommandContext


@pytest.mark.unit_test
def test_optional_matrices(empty_study_920: FileStudy, command_context: CommandContext) -> None:
    # Create an area containing 1 thermal cluster and 1 short-term storage
    study = empty_study_920
    version = study.config.version
    cmd = CreateArea(area_name="fr", command_context=command_context, study_version=version)
    output = cmd.apply(study)
    assert output.status
    cmd = CreateCluster(
        area_id="fr",
        parameters=ThermalClusterCreation(name="thermal_cluster"),
        command_context=command_context,
        study_version=version,
    )
    output = cmd.apply(study)
    assert output.status
    cmd = CreateSTStorage(
        command_context=command_context,
        area_id="fr",
        parameters=STStorageCreation(name="sts"),
        study_version=version,
    )
    output = cmd.apply(study)
    assert output.status

    expected_content = np.zeros((8760, 1)).tolist()
    for url in [
        ["input", "thermal", "series", "fr", "thermal_cluster", "fuelCost"],
        ["input", "thermal", "series", "fr", "thermal_cluster", "CO2Cost"],
        ["input", "st-storage", "series", "fr", "sts", "cost_injection"],
        ["input", "st-storage", "series", "fr", "sts", "cost_withdrawal"],
        ["input", "st-storage", "series", "fr", "sts", "cost_level"],
        ["input", "st-storage", "series", "fr", "sts", "cost_variation_injection"],
        ["input", "st-storage", "series", "fr", "sts", "cost_variation_withdrawal"],
    ]:
        # Removes the file from the fs
        study.tree.get_node(url).delete()

        # Ensures we can still fetch its content without raising an issue as these files are optional for the Simulator.
        content = study.tree.get(url)
        assert content["data"] == expected_content

    # Ensures the normalization succeeds even if the files are missing
    study.tree.normalize()

    # Removes a file that's not optional for the Simulator
    url = ["input", "thermal", "series", "fr", "thermal_cluster", "series"]
    study.tree.get_node(url).delete()

    # Ensures retrieving its content raises an Exception
    with pytest.raises(
        ChildNotFoundError,
        match="404: File 'input/thermal/series/fr/thermal_cluster/series.txt' not found in the study ''",
    ):
        study.tree.get(url)

    # Ensures normalization also fails
    with pytest.raises(
        ChildNotFoundError,
        match="404: File 'input/thermal/series/fr/thermal_cluster/series.txt' not found in the study ''",
    ):
        study.tree.normalize()
