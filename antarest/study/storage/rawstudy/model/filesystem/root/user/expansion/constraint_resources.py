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
from antarest.matrixstore.matrix_uri_mapper import MatrixUriMapper
from antarest.study.storage.rawstudy.model.filesystem.bucket_node import BucketNode
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig


class ExpansionConstraintResources(BucketNode):
    def __init__(self, matrix_mapper: MatrixUriMapper, config: FileStudyTreeConfig):
        super().__init__(matrix_mapper, config, None)
