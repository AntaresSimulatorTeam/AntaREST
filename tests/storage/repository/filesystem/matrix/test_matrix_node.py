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
from typing import List, Optional
from unittest.mock import Mock

import pandas as pd
from typing_extensions import override

from antarest.matrixstore.matrix_uri_mapper import MatrixUriMapper, MatrixUriMapperFactory, NormalizedMatrixUriMapper
from antarest.study.model import STUDY_VERSION_8_8, MatrixFrequency
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixNode

MOCK_MATRIX = pd.DataFrame([[1, 2], [3, 4]])


class MockMatrixNode(MatrixNode):
    def __init__(self, matrix_mapper: MatrixUriMapper, config: FileStudyTreeConfig) -> None:
        super().__init__(
            config=config,
            matrix_mapper=matrix_mapper,
            freq=MatrixFrequency.ANNUAL,
        )

    @override
    def parse_as_dataframe(self, file_path: Optional[Path] = None) -> pd.DataFrame:
        return MOCK_MATRIX

    @override
    def write_dataframe(self, df: pd.DataFrame) -> None:
        df.to_csv(self.config.path, sep="\t", header=False, index=False)

    def check_errors(self, data: str, url: Optional[List[str]] = None, raising: bool = False) -> List[str]:
        pass  # not used


def test_normalize_denormalize_methods(tmp_path: Path) -> None:
    file = tmp_path / "matrix.txt"

    matrix_mapper = MatrixUriMapperFactory(matrix_service=Mock()).create(NormalizedMatrixUriMapper.NORMALIZED)
    config = FileStudyTreeConfig(study_path=file, path=file, study_id="mi-id", version=STUDY_VERSION_8_8)

    node = MockMatrixNode(matrix_mapper=matrix_mapper, config=config)

    assert node.get_matrix_nodes_to_normalize() == [node]
    assert node.get_matrix_nodes_to_denormalize() == []

    link = file.parent / f"{file.name}.link"
    link.write_text("my-id")
    node = MockMatrixNode(matrix_mapper=matrix_mapper, config=config)

    assert node.get_matrix_nodes_to_normalize() == []
    assert node.get_matrix_nodes_to_denormalize() == [node]
