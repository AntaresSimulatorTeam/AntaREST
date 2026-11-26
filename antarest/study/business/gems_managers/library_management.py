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
from antarest.study.business.model.gems.library import GemsModelsProperties
from antarest.study.business.study_interface import StudyInterface


class GemsLibraryManager:
    def get_model_properties(self, study: StudyInterface, library_id: str, model_id: str) -> list[GemsModelsProperties]:
        return study.get_study_dao().get_properties_ids(library_id, model_id)
