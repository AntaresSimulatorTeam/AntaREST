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

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from antarest.output.repository import OutputRepository
from antarest.study.model import Study


def test_disk_usage_updates_preserve_unarchiving_date(db_session: Session) -> None:
    db_session.add(Study(id="study", version="9.2"))
    db_session.commit()
    repository = OutputRepository(db_session)
    date = datetime(2026, 1, 1)

    repository.save_unarchiving_date("study", "output", date)
    repository.save_disk_usage("study", "output", 42)
    output = repository.get("study", "output")
    assert output is not None
    assert (output.last_unarchiving_date, output.disk_space_bytes) == (date, 42)

    repository.invalidate_disk_usage("study", "output")
    output = repository.get("study", "output")
    assert output is not None
    assert (output.last_unarchiving_date, output.disk_space_bytes) == (date, None)

    repository.save_disk_usage("study", "output", 21)
    repository.save_unarchiving_date("study", "output", date + timedelta(days=1))
    output = repository.get("study", "output")
    assert output is not None
    assert (output.last_unarchiving_date, output.disk_space_bytes) == (date + timedelta(days=1), None)

    repository.save_disk_usage("study", "other-output", 0)
    output = repository.get("study", "other-output")
    assert output is not None
    assert (output.last_unarchiving_date, output.disk_space_bytes) == (None, 0)
