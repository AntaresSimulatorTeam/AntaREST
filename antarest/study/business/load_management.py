# Copyright (c) 2024, RTE (https://www.rte-france.com)
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
import typing as t

from antarest.study.model import MatrixFormat, Study
from antarest.study.storage.storage_service import StudyStorageService


class LoadOutput:
    pass


class LoadManager:
    def __init__(self, storage_service: StudyStorageService) -> None:
        self.storage_service = storage_service

    def get_load_matrix(self, study: Study, area_id: str, matrix_format: t.Optional[MatrixFormat]) -> LoadOutput:
        return LoadOutput()
