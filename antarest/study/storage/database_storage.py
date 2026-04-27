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
import logging
from pathlib import Path
from typing import BinaryIO, Iterator

from typing_extensions import override

from antarest.core.config import Config
from antarest.matrixstore.model import MatrixReference
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.model import RawStudy, Study
from antarest.study.storage.study_storage_interface import IStudyStorage
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants

logger = logging.getLogger(__name__)


class DatabaseStudyStorage(IStudyStorage):
    def __init__(
        self, config: Config, matrix_service: ISimpleMatrixService, generator_matrix_constants: GeneratorMatrixConstants
    ):
        self._matrix_service = matrix_service
        self._generator_matrix_constants = generator_matrix_constants
        self._config = config

    @override
    def copy(self, src_study: Study, new_study: RawStudy) -> RawStudy:
        # TODO
        raise NotImplementedError()

    @override
    def write_study_for_archive(self, study: RawStudy, dst_path: Path) -> None:
        # Nothing to do
        pass

    @override
    def export_study(self, study: Study, dst_path: Path) -> None:
        # TODO
        raise NotImplementedError()

    @override
    def get_disk_usage(self, study: Study) -> int:
        return 0

    @override
    def yield_matrix_references(self, study: Study) -> Iterator[MatrixReference]:
        # Nothing to do
        yield from ()

    @override
    def normalize_study(self, study: Study) -> None:
        # Nothing to do
        pass

    @override
    def import_study(self, study: RawStudy, stream: BinaryIO) -> RawStudy:
        # TODO
        raise NotImplementedError()
