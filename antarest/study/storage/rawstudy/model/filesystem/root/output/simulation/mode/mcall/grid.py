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

from typing import List, Optional, cast

import pandas as pd
from typing_extensions import override

from antarest.core.exceptions import MustNotModifyOutputException
from antarest.core.model import JSON
from antarest.matrixstore.uri_resolver_service import UriResolverService
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.lazy_node import LazyNode
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcall.digest import DigestSynthesis


class OutputSimulationModeMcAllGrid(FolderNode):
    @override
    def build(self) -> TREE:
        files = [d.stem for d in self.config.path.iterdir()]
        children: TREE = {}
        for file in files:
            synthesis_class = DigestSynthesis if file == "digest" else OutputSynthesis
            children[file] = synthesis_class(self.context, self.config.next_file(f"{file}.txt"))
        return children


class OutputSynthesis(LazyNode[JSON, bytes, bytes]):
    def __init__(self, context: UriResolverService, config: FileStudyTreeConfig):
        super().__init__(context, config)

    @override
    def get_lazy_content(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
    ) -> str:
        return f"matrix://{self.config.path.name}"  # prefix used by the front to parse the back-end response

    @override
    def load(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        formatted: bool = True,
    ) -> JSON:
        file_path = self.config.path
        df = pd.read_csv(file_path, sep="\t")
        df.fillna("", inplace=True)  # replace NaN values for the front-end
        output = df.to_dict(orient="split")
        del output["index"]
        return cast(JSON, output)

    @override
    def dump(self, data: bytes, url: Optional[List[str]] = None) -> None:
        raise MustNotModifyOutputException(self.config.path.name)

    @override
    def check_errors(self, data: str, url: Optional[List[str]] = None, raising: bool = False) -> List[str]:
        if not self.config.path.exists():
            msg = f"{self.config.path} not exist"
            if raising:
                raise ValueError(msg)
            return [msg]
        return []

    @override
    def normalize(self) -> None:
        pass  # shouldn't be normalized as it's an output file

    @override
    def denormalize(self) -> None:
        pass  # shouldn't be denormalized as it's an output file
