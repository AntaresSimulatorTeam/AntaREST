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

import datetime
from pathlib import Path
from unittest.mock import Mock

from antarest.core.utils.utils import current_time
from antarest.maintenance.tasks.auto_archive import archive_old_studies
from antarest.maintenance.tasks.common import BackGroundTaskStatus
from antarest.output.dbmodel import Output
from antarest.study.model import DEFAULT_WORKSPACE_NAME
from antarest.study.repository import StudyMetadataRepository
from tests.helpers import create_raw_study, create_variant_study, with_db_context


@with_db_context
def test_output_archival_includes_variants_but_excludes_external_and_archived_studies(tmp_path: Path) -> None:
    now = current_time()
    repository = StudyMetadataRepository()
    repository.session.add_all(
        [
            create_raw_study(id="external", workspace="external", updated_at=now),
            create_raw_study(id="archived", workspace=DEFAULT_WORKSPACE_NAME, archived=True, updated_at=now),
            create_variant_study(id="variant", updated_at=now),
        ]
    )
    repository.session.commit()
    study_service, output_service = Mock(repository=repository), Mock()
    output_service.initialize_outputs_metadata.return_value = [
        Output(study_id="variant", output_id="output", last_access=now - datetime.timedelta(days=61), archived=False)
    ]

    result = archive_old_studies(study_service, output_service, 60, 7, True, tmp_path)

    assert result.status == BackGroundTaskStatus.SUCCESS
    assert result.archived_outputs == 1
    assert result.archived_studies == 0
    output_service.initialize_outputs_metadata.assert_called_once_with("variant", dry_run=True)
