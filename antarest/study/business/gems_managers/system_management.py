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
from antarest.study.business.model.gems.system import GemsProperties
from antarest.study.business.study_interface import StudyInterface


class GemsSystemManager:
    def get_component_properties(self, study: StudyInterface, component_id: str) -> list[GemsProperties]:
        return study.get_study_dao().get_properties(component_id)
