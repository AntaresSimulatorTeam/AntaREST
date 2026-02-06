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


def test_area_with_no_clusters_are_absent_from_clusters_dict(filestudy_dao: FileStudyTreeDao) -> None:
    filestudy_dao.save_area("germany")
    filestudy_dao.save_area("italy")

    filestudy_dao.save_thermal("germany", ThermalCluster(id="gas", name="Gas"))

    clusters = filestudy_dao.get_all_thermals()

    assert "italy" not in clusters
    assert "germany" in clusters
    assert "gas" in clusters["germany"]
