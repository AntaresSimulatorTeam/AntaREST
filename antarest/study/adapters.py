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
from pathlib import Path

from typing_extensions import override

from antarest.core.model import JSON
from antarest.output.service import OutputService
from antarest.output.storage.output_storage import OutputDetails, OutputMetadata
from antarest.study.model import MatrixFrequency, MatrixIndex
from antarest.study.service import IOutputsAccess


def adapt_output_service_to_study_service(output_service: OutputService) -> IOutputsAccess:
    """
    Creates a small wrapper of the output service to provides basic operations on outputs to study service.
    """

    class OutputServiceAdapter(IOutputsAccess):
        @override
        def list_outputs(self, study_id: str) -> list[OutputMetadata]:
            return list(output_service.list_outputs(study_id))

        @override
        def get_outputs_details(self, study_id: str) -> dict[str, OutputDetails]:
            return {o.name: o for o in output_service.get_output_details(study_id)}

        @override
        def copy_output(self, src_study_id: str, target_study_id: str, output_id: str) -> None:
            return output_service.copy_output(src_study_id, target_study_id, output_id)

        @override
        def delete_output(self, study_id: str, output_id: str) -> None:
            output_service.delete_output(study_id, output_id)

        @override
        def write_output_to_dir(self, study_id: str, output_id: str, parent_dir: Path) -> None:
            output_service.write_output_to_dir(study_id, output_id, parent_dir)

        @override
        def archive_output(self, study_id: str, output_id: str) -> None:
            output_service.archive_output(study_id, output_id)

        @override
        def get_disk_usage(self, study_id: str, output_id: str) -> int:
            return output_service.get_disk_usage(study_id, output_id)

        @override
        def import_outputs(self, outputs_dir: Path, study_id: str) -> None:
            output_service.import_outputs(outputs_dir, study_id)

        @override
        def get_output_time_index(self, study_id: str, output_id: str, frequency: MatrixFrequency) -> MatrixIndex:
            return output_service.get_output_time_index(study_id, output_id, frequency)

        @override
        def get_output_raw_content(
            self, study_id: str, output_id: str, url: list[str], formatted: bool
        ) -> bytes | JSON:
            return output_service.get_output_raw_content(study_id, output_id, url, formatted)

    return OutputServiceAdapter()
