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

from antarest.core.serde.ini_reader import SimpleKeyValueReader
from antarest.core.serde.ini_writer import SimpleKeyValueWriter
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix_storage_context import MatrixStorageContext


class ExpansionSettings(IniFileNode):
    """
    Since version >= 800:

    - master: str = "integer" or "relaxed". default="integer"
    - uc_type: str = "expansion_fast" or "expansion_accurate". default="expansion_fast"
    - optimality_gap: float = 1
    - relative_gap: float = 1e-6
    - relaxed_optimality_gap: float = 1e-5
    - max_iteration: int = 1000
    - solver: str = "Cbc", "Coin" or "Xpress". default="Cbc"
    - log_level: int = 0, 1, 2, 3. default=0
    - separation_parameter: float = 0.5  # 0 < separation_parameter <= 1
    - batch_size: int = 0
    - yearly-weights: str = filename. default = ""
    - additional-constraints: str = filename. default = ""
    """

    def __init__(self, matrix_storage_context: MatrixStorageContext, config: FileStudyTreeConfig):
        super().__init__(config, reader=SimpleKeyValueReader(), writer=SimpleKeyValueWriter())
