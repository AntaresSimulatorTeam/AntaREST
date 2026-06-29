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
from antarest.study.business.model.reserve_definition_model import ReserveDefinition, ReserveType
from antarest.study.dao.api.study_dao import StudyDao
from tests.study.dao.utils import save_area


def _reserve(name: str, reserve_type: ReserveType = ReserveType.UP, **overrides) -> ReserveDefinition:
    base = dict(
        name=name,
        type=reserve_type,
        failure_cost=10.0,
        spillage_cost=5.0,
        reference_activation_duration=3,
        power_activation_ratio=0.4,
        energy_activation_ratio=0.9,
    )
    base.update(overrides)
    return ReserveDefinition(**base)


def test_cascade_delete_on_area_removal(dao_10_0: StudyDao) -> None:
    save_area(dao_10_0, "paris")
    dao_10_0.save_reserve_definitions({"paris": [_reserve("R1")]})

    dao_10_0.delete_area("paris")

    assert dao_10_0.get_all_reserve_definitions() == {}
