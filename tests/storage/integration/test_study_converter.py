# Copyright (c) 2025, RTE (https://www.rte-france.com)
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
from pathlib import Path

from antarest.study.service import StudyService
from tests.helpers import with_admin_user
from tests.storage.integration.conftest import UUID


@with_admin_user
def test_convert_study(storage_service: StudyService, tmp_path: Path) -> None:
    """
    For the moment, it only ensures the method doesn't crash
    """
    source_path = tmp_path / "studies" / UUID
    new_path = tmp_path / "studies" / "new_study" / UUID
    outputs_before = [f.name for f in (source_path / "output").iterdir()]
    storage_service.write_study_as_file_study(UUID, new_path)
    # Checks the output folder was copied
    assert [f.name for f in (new_path / "output").iterdir()] == outputs_before
