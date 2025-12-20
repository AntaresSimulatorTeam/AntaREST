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

from antarest.study.business.output.utils import QueryFileType
from antarest.study.model import MatrixIndex, StudyDownloadLevelDTO, StudySimResultDTO
from antarest.study.output.output_model import OutputVariablesList
from antarest.study.output.output_storage import IOutputStorage, OutputStorageType
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcall.digest import DigestUI


class ParquetOutputStorage(IOutputStorage):
    @property
    def storage_type(self) -> OutputStorageType:
        return OutputStorageType.PARQUET

    def import_output(self, study_id: str, output: BinaryIO | Path, output_name: Optional[str] = None) -> Optional[str]:
        raise NotImplementedError()

    def get_study_sim_result(self, study_id: str) -> List[StudySimResultDTO]:
        raise NotImplementedError()

    def delete_output(self, study_id: str, output_id: str) -> None:
        raise NotImplementedError()

    def export_output(self, study_id: str, output_id: str, target: Path) -> None:
        raise NotImplementedError()

    def output_exists(self, study_id: str, output_id: str) -> bool:
        raise NotImplementedError()

    def is_output_archived(self, study_id: str, output_id: str) -> bool:
        raise NotImplementedError()

    def archive_study_output(self, study_id: str, output_id: str) -> None:
        raise NotImplementedError()

    def unarchive_study_output(self, study_id: str, output_id: str) -> None:
        raise NotImplementedError()

    def get_digest(self, study_id: str, output_id: str) -> DigestUI:
        raise NotImplementedError()

    def get_output_time_index(self, study_id: str, output_id: str, frequency: StudyDownloadLevelDTO) -> MatrixIndex:
        raise NotImplementedError()

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

    def extract_variables_list(self, study_id: str, output_id: str) -> OutputVariablesList:
        raise NotImplementedError()
