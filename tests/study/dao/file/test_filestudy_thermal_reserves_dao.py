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


from antarest.study.business.model.area_properties_model import AreaProperties
from antarest.study.business.model.reserve_definition_model import ReserveDefinition, ReserveType
from antarest.study.business.model.thermal_cluster_model import ThermalCluster
from antarest.study.business.model.thermal_reserve_certification_model import ThermalReserveCertification
from antarest.study.model import STUDY_VERSION_10_0


def test_symmetries_and_certifications_do_not_overwrite_each_other(fs_dao_930_and_matrix_service) -> None:
    # Build a v10.0 FS DAO.
    dao, _ = fs_dao_930_and_matrix_service
    dao.get_file_study().config.version = STUDY_VERSION_10_0
    # Create 1 area with 2 thermal clusters and 4 reserves
    dao.save_areas_with_properties({"fr": AreaProperties()})
    dao.save_thermals({"fr": [ThermalCluster(name="th1"), ThermalCluster(name="th2")]})
    reserves = []
    for reserve_name in ["r1", "r2", "r3", "r4"]:
        reserves.append(ReserveDefinition(name=reserve_name, type=ReserveType.DOWN))
    dao.save_reserve_definitions({"fr": reserves})

    # Save 2 symmetries. Then 1 certification. Ensures the certification writing didn't affect the symmetries.
    dao.save_thermal_reserve_symmetries({"fr": {"th1": [["r1", "r2"], ["r3", "r4"]]}})
    dao.save_thermal_reserve_certifications({"fr": {"r1": {"th2": ThermalReserveCertification()}}})

    assert dao.get_thermal_reserve_symmetries("fr") == {"th1": [["r1", "r2"], ["r3", "r4"]]}
    assert dao.get_thermal_reserve_certifications("fr") == {"th1": [["r1", "r2"], ["r3", "r4"]]}
