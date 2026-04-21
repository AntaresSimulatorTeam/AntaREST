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
from antarest.study.model import Study
from antarest.study.storage.database_study_storage import IDataBaseStudyStorage
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy


class VariantDataBaseStudyStorage(IDataBaseStudyStorage):
    def clear_snapshot(self, variant_study: VariantStudy) -> None:
        raise NotImplementedError()

    def create_snapshot(self, study: Study) -> None:
        raise NotImplementedError()
