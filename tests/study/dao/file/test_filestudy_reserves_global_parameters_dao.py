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

import pytest

from antarest.core.exceptions import AreaNotFound
from antarest.study.business.model.reserves_global_parameters_model import ReservesGlobalParameters
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao
from tests.study.dao.utils import save_area


def test_save_raises_for_nonexistent_area(filestudy_dao: FileStudyTreeDao) -> None:
    with pytest.raises(AreaNotFound):
        filestudy_dao.save_reserves_global_parameters({"nonexistent": ReservesGlobalParameters()})


def test_save_validates_all_areas_before_writing(filestudy_dao: FileStudyTreeDao) -> None:
    save_area(filestudy_dao, "paris")

    with pytest.raises(AreaNotFound):
        filestudy_dao.save_reserves_global_parameters(
            {
                "paris": ReservesGlobalParameters(reference_activation_duration_up=42),
                "nonexistent": ReservesGlobalParameters(),
            }
        )
