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
from antarest.core.exceptions import GemsLibraryNotFound, GemsModelNotFound
from antarest.study.business.model.gems.library import GemsModelProperty
from antarest.study.business.study_interface import StudyInterface


class GemsLibraryManager:
    def get_model_properties(self, study: StudyInterface, library_id: str, model_id: str) -> list[GemsModelProperty]:
        library = study.get_study_dao().get_library()
        if library is None or library.id != library_id:
            raise GemsLibraryNotFound(f"Library '{library_id}' not found for study '{study.id}'")

        for model in library.models:
            if model.id == model_id:
                return [GemsModelProperty(name=prop.id) for prop in model.properties]

        raise GemsModelNotFound(f"Model '{model_id}' not found in library '{library_id}' for study '{study.id}'")
