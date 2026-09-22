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
from antarest.study.business.model.thermal_cluster_model import ThermalCluster
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao
from tests.study.dao.utils import save_area


def test_area_with_no_clusters_are_absent_from_clusters_dict(filestudy_dao: FileStudyTreeDao) -> None:
    save_area(filestudy_dao, "germany")
    save_area(filestudy_dao, "italy")

    filestudy_dao.save_thermals({"germany": [ThermalCluster(id="gas", name="Gas")]})

    clusters = filestudy_dao.get_all_thermals()

    assert "italy" not in clusters
    assert "germany" in clusters
    assert "gas" in clusters["germany"]
