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
from typing import BinaryIO, Iterator, List, Optional, Sequence

import pandas as pd
from typing_extensions import override

from antarest.study.model import MatrixFrequency, MatrixIndex, StudySimResultDTO
from antarest.study.output.output_model import OutputVariablesList
from antarest.study.output.output_storage import IOutputStorage, OutputStorageType
from antarest.study.output.utils import QueryFileType
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcall.digest import DigestUI


class ParquetOutputStorage(IOutputStorage):
    @property
    @override
    def storage_type(self) -> OutputStorageType:
        return OutputStorageType.PARQUET

    @override
    def import_output(self, study_id: str, output: BinaryIO | Path, output_name: Optional[str] = None) -> Optional[str]:
        raise NotImplementedError()

    @override
    def get_study_sim_result(self, study_id: str) -> List[StudySimResultDTO]:
        raise NotImplementedError()

    @override
    def delete_output(self, study_id: str, output_id: str) -> None:
        raise NotImplementedError()

    @override
    def export_output(self, study_id: str, output_id: str, target: Path) -> None:
        raise NotImplementedError()

    @override
    def output_exists(self, study_id: str, output_id: str) -> bool:
        raise NotImplementedError()

    @override
    def is_output_archived(self, study_id: str, output_id: str) -> bool:
        raise NotImplementedError()

    @override
    def archive_study_output(self, study_id: str, output_id: str) -> None:
        raise NotImplementedError()

    @override
    def unarchive_study_output(self, study_id: str, output_id: str) -> None:
        raise NotImplementedError()

    @override
    def get_digest(self, study_id: str, output_id: str) -> DigestUI:
        raise NotImplementedError()

    @override
    def get_output_time_index(self, study_id: str, output_id: str, frequency: MatrixFrequency) -> MatrixIndex:
        raise NotImplementedError()

    @override
    def aggregate_output_data(
        self,
        study_id: str,
        output_id: str,
        query_file: QueryFileType,
        frequency: MatrixFrequency,
        ids_to_consider: Sequence[str],
        columns_names: Sequence[str],
        transform_columns_headers: bool,
        mc_years: Optional[Sequence[int]] = None,
    ) -> Iterator[pd.DataFrame]:
        raise NotImplementedError()

    @override
    def extract_variables_list(self, study_id: str, output_id: str) -> OutputVariablesList:
        raise NotImplementedError()
