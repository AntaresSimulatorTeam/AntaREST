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

from typing_extensions import override

from antarest.study.output.output_service import OutputService
from antarest.study.service import IOutputServiceAccess
from antarest.study.storage.rawstudy.model.filesystem.config.model import Simulation


def adapt_output_service_to_study_service(output_service: OutputService) -> IOutputServiceAccess:
    """
    Creates a small wrapper of the output service to provides basic operations on outputs to study service.
    """

    class OutputServiceAdapter(IOutputServiceAccess):
        @override
        def list_outputs(self, study_id: str) -> dict[str, Simulation]:
            return output_service.get_simulations(study_id)

        @override
        def copy_outputs(
            self, src_study_id: str, target_study_id: str, with_outputs: bool | None, output_ids: list[str]
        ) -> None:
            return output_service.copy_outputs(src_study_id, target_study_id, with_outputs, output_ids)

        @override
        def delete_outputs(self, study_id: str) -> None:
            for output in output_service.get_study_sim_result(study_id):
                output_service.delete_output(study_id, output.name)

        @override
        def write_outputs_to_dir(self, study_id: str, parent_dir: Path, outputs: list[str] | None = None) -> None:
            if outputs is None:
                outputs = [o.name for o in output_service.get_study_sim_result(study_id)]
            for output in outputs:
                output_service.write_output_to_dir(study_id, output, parent_dir)

    return OutputServiceAdapter()
