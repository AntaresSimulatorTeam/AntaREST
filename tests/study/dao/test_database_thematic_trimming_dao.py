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


from antarest.study.business.model.thematic_trimming_model import (
    ThematicTrimming,
    get_thematic_trimming_fields_according_to_version,
)
from antarest.study.dao.api.study_dao import StudyDao


def test_nominal_case(dao: StudyDao) -> None:
    disabled = {"ov_cost": False, "op_cost": False, "mrg_price": False, "co2_emis": False, "dtg_by_plant": False}
    dao.save_thematic_trimming(ThematicTrimming(**disabled))

    result = dao.get_thematic_trimming()
    version_fields = get_thematic_trimming_fields_according_to_version(dao.get_version())

    for field, value in disabled.items():
        assert getattr(result, field) is value, f"{field} should be False"

    for field in version_fields - disabled.keys():
        assert getattr(result, field) is True, f"{field} should default to True"
