import csv
import typing as t

import pandas as pd

from antarest.core.model import JSON
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.lazy_node import LazyNode


class OutputSimulationModeMcAllGrid(FolderNode):
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

    def get_lazy_content(
        self,
        url: t.Optional[t.List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
    ) -> str:
        return f"matrix://{self.config.path.name}"

    def load(
        self,
        url: t.Optional[t.List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        formatted: bool = True,
    ) -> JSON:
        file_path = self.config.path
        df = pd.read_csv(file_path, sep="\t")
        output = df.to_dict(orient="split")
        del output["index"]
        return t.cast(JSON, output)

    def dump(self, data: bytes, url: t.Optional[t.List[str]] = None) -> None:
        self.config.path.parent.mkdir(exist_ok=True, parents=True)
        self.config.path.write_bytes(data)

    def check_errors(self, data: str, url: t.Optional[t.List[str]] = None, raising: bool = False) -> t.List[str]:
        if not self.config.path.exists():
            msg = f"{self.config.path} not exist"
            if raising:
                raise ValueError(msg)
            return [msg]
        return []

    def normalize(self) -> None:
        pass  # no external store in this node

    def denormalize(self) -> None:
        pass  # no external store in this node


class DigestSynthesis(OutputSynthesis):
    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        super().__init__(context, config)

    def load(
        self,
        url: t.Optional[t.List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        formatted: bool = True,
    ) -> JSON:
        file_path = self.config.path
        with open(file_path, "r") as f:
            csv_file = csv.reader(f, delimiter="\t")
            longest_row = 0
            for row in csv_file:
                row_length = len(row)
                if row_length > longest_row:
                    longest_row = row_length

        with open(file_path, "r") as f:
            csv_file = csv.reader(f, delimiter="\t")
            new_rows = []
            for row in csv_file:
                new_row = row
                n = len(row)
                if n < longest_row:
                    difference = longest_row - n
                    new_row += [""] * difference
                new_rows.append(row)
        df = pd.DataFrame(data=new_rows)
        output = df.to_dict(orient="split")
        del output["index"]
        return t.cast(JSON, output)
