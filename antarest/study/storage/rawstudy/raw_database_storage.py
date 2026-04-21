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
from antarest.study.model import RawStudy
from antarest.study.storage.database_study_storage import IDataBaseStudyStorage


class RawDataBaseStudyStorage(IDataBaseStudyStorage):
    def update_from_raw_metadata(self, study: RawStudy, fallback_on_default: bool | None = False) -> None:
        # Nothing to do
        pass

    def update_name_and_version_from_raw_meta(self, study: RawStudy) -> bool:
        # Nothing to do
        return True
