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

import logging

from typing_extensions import override

from antarest.study.storage.rawstudy.model.filesystem.bucket_node import BucketNode
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.desktop import Desktop
from antarest.study.storage.rawstudy.model.filesystem.root.input.input import Input
from antarest.study.storage.rawstudy.model.filesystem.root.layers.layers import Layers
from antarest.study.storage.rawstudy.model.filesystem.root.output.output import Output
from antarest.study.storage.rawstudy.model.filesystem.root.settings.settings import Settings
from antarest.study.storage.rawstudy.model.filesystem.root.study_antares import StudyAntares
from antarest.study.storage.rawstudy.model.filesystem.root.user.user import User

logger = logging.getLogger(__name__)


class FileStudyTree(FolderNode):
    """
    Top level node of antares tree structure
    """

    @override
    def build(self) -> TREE:
        children: TREE = {
            "Desktop": Desktop(self.config.next_file("Desktop.ini")),
            "study": StudyAntares(self.config.next_file("study.antares")),
            "settings": Settings(self.matrix_mapper, self.config.next_file("settings")),
            "layers": Layers(self.matrix_mapper, self.config.next_file("layers")),
            "input": Input(self.matrix_mapper, self.config.next_file("input")),
            "user": User(self.matrix_mapper, self.config.next_file("user")),
        }

        if (self.config.path / "logs").exists():
            children["logs"] = BucketNode(self.matrix_mapper, self.config.next_file("logs"))

        if self.config.outputs:
            output_config = self.config.next_file("output")
            output_config.path = self.config.output_path or output_config.path
            children["output"] = Output(self.matrix_mapper, output_config)

        return children
