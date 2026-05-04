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
from antarest.matrixstore.matrix_uri_mapper import MatrixStorageContext
from antarest.study.storage.rawstudy.model.filesystem.bucket_node import BucketNode, RegisteredFile
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.root.user.expansion.adequacy_criterion import (
    ExpansionAdequacyCriterion,
)
from antarest.study.storage.rawstudy.model.filesystem.root.user.expansion.candidates import ExpansionCandidates
from antarest.study.storage.rawstudy.model.filesystem.root.user.expansion.constraint_resources import (
    ExpansionConstraintResources,
)
from antarest.study.storage.rawstudy.model.filesystem.root.user.expansion.matrix_resources import (
    ExpansionMatrixResources,
)
from antarest.study.storage.rawstudy.model.filesystem.root.user.expansion.sensitivity import SensitivityConfig
from antarest.study.storage.rawstudy.model.filesystem.root.user.expansion.settings import ExpansionSettings


class Expansion(BucketNode):
    registered_files = [
        RegisteredFile(key="candidates", node=ExpansionCandidates, filename="candidates.ini"),
        RegisteredFile(key="settings", node=ExpansionSettings, filename="settings.ini"),
        RegisteredFile(key="capa", node=ExpansionMatrixResources),
        RegisteredFile(key="weights", node=ExpansionMatrixResources),
        RegisteredFile(key="constraints", node=ExpansionConstraintResources),
        RegisteredFile(key="sensitivity", node=SensitivityConfig),
        RegisteredFile(key="adequacy_criterion", node=ExpansionAdequacyCriterion),
    ]

    def __init__(self, matrix_storage_context: MatrixStorageContext, config: FileStudyTreeConfig):
        super().__init__(matrix_storage_context, config, self.registered_files)
