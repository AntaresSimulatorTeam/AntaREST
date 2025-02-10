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

import typing as t

import pandas as pd
from typing_extensions import override

from antarest.core.exceptions import MustNotModifyOutputException
from antarest.core.model import JSON
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.lazy_node import LazyNode


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
    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        super().__init__(context, config)

    @override
    def get_lazy_content(
        self,
        url: t.Optional[t.List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
    ) -> str:
        return f"matrix://{self.config.path.name}"  # prefix used by the front to parse the back-end response

    @override
    def load(
        self,
        url: t.Optional[t.List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        formatted: bool = True,
    ) -> JSON:
        file_path = self.config.path
        df = pd.read_csv(file_path, sep="\t")
        df.fillna("", inplace=True)  # replace NaN values for the front-end
        output = df.to_dict(orient="split")
        del output["index"]
        return t.cast(JSON, output)

    @override
    def dump(self, data: bytes, url: t.Optional[t.List[str]] = None) -> None:
        raise MustNotModifyOutputException(self.config.path.name)

    @override
    def check_errors(self, data: str, url: t.Optional[t.List[str]] = None, raising: bool = False) -> t.List[str]:
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


class DigestSynthesis(OutputSynthesis):
    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        super().__init__(context, config)

    @override
    def load(
        self,
        url: t.Optional[t.List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        formatted: bool = True,
    ) -> JSON:
        file_path = self.config.path
        with open(file_path, "r") as f:
            df = _parse_digest_file(f)

        df.fillna("", inplace=True)  # replace NaN values for the front-end
        output = df.to_dict(orient="split")
        del output["index"]
        return t.cast(JSON, output)


def _parse_digest_file(digest_file: t.TextIO) -> pd.DataFrame:
    """
    Parse a digest file as a whole and return a single DataFrame.

    The `digest.txt` file is a TSV file containing synthetic results of the simulation.
    This file contains several data tables, each being separated by empty lines
    and preceded by a header describing the nature and dimensions of the table.

    Note that rows in the file may have different number of columns.
    """

    # Reads the file and find the maximum number of columns in any row
    data = [row.split("\t") for row in digest_file.read().splitlines()]
    max_cols = max(len(row) for row in data)

    # Adjust the number of columns in each row
    data = [row + [""] * (max_cols - len(row)) for row in data]

    # Returns a DataFrame from the data (do not convert values to float)
    return pd.DataFrame(data=data, columns=[str(i) for i in range(max_cols)], dtype=object)
