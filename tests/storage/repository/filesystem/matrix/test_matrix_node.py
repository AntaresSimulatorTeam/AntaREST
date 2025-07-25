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

from antarest.matrixstore.matrix_uri_mapper import MatrixUriMapper, MatrixUriMapperFactory, NormalizedMatrixUriMapper
from antarest.study.model import STUDY_VERSION_8_8
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency, MatrixNode

MOCK_MATRIX = pd.DataFrame([[1, 2], [3, 4]])


class MockMatrixNode(MatrixNode):
    def __init__(self, matrix_mapper: MatrixUriMapper, config: FileStudyTreeConfig) -> None:
        super().__init__(
            config=config,
            matrix_mapper=matrix_mapper,
            freq=MatrixFrequency.ANNUAL,
        )

    def parse_as_dataframe(self, file_path: Optional[Path] = None) -> pd.DataFrame:
        return MOCK_MATRIX

    def check_errors(self, data: str, url: Optional[List[str]] = None, raising: bool = False) -> List[str]:
        pass  # not used


class TestMatrixNode:
    def test_normalize(self, tmp_path: Path):
        file = tmp_path / "matrix.json"
        file.touch()

        matrix_service = Mock()
        matrix_service.create.return_value = "my-id"

        factory = MatrixUriMapperFactory(matrix_service=matrix_service)
        matrix_mapper = factory.create(NormalizedMatrixUriMapper.NORMALIZED)

        node = MockMatrixNode(
            matrix_mapper=matrix_mapper,
            config=FileStudyTreeConfig(study_path=file, path=file, study_id="mi-id", version=STUDY_VERSION_8_8),
        )

        node.normalize()

        # check the result
        assert node.matrix_mapper.get_link_content(node) == "matrix://my-id"
        assert not file.exists()
        matrix_service.create.assert_called_once()
        args = matrix_service.create.call_args.args
        assert len(args) == 1
        assert MOCK_MATRIX.equals(args[0])

    def test_denormalize(self, tmp_path: Path):
        file = tmp_path / "matrix.json"

        link = file.parent / f"{file.name}.link"
        link.write_text("my-id")

        matrix_service = Mock()
        matrix_service.get.return_value = MOCK_MATRIX

        factory = MatrixUriMapperFactory(matrix_service=matrix_service)
        matrix_mapper = factory.create(NormalizedMatrixUriMapper.NORMALIZED)

        node = MockMatrixNode(
            matrix_mapper=matrix_mapper,
            config=FileStudyTreeConfig(study_path=file, path=file, study_id="mi-id", version=STUDY_VERSION_8_8),
        )

        node.denormalize()

        # check the result
        assert not link.exists()
        actual = pd.read_csv(file, sep="\t", header=None)
        assert actual.equals(MOCK_MATRIX)
