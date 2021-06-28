from io import StringIO
from pathlib import Path
from typing import Optional, List, IO

import pandas as pd  # type: ignore
from pandas.errors import EmptyDataError  # type: ignore

from antarest.common.custom_types import JSON, SUB_JSON
from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.lazy_node import LazyNode
from antarest.storage.repository.filesystem.context import ContextServer
from antarest.storage.repository.filesystem.matrix.matrix import MatrixNode


class InputSeriesMatrix(MatrixNode):
    """
    Generic node to handle input matrix behavior
    """

    def __init__(
        self,
        context: ContextServer,
        config: StudyConfig,
        nb_columns: Optional[int] = None,
    ):
        super().__init__(context=context, config=config, freq="hourly")
        self.nb_columns = nb_columns

    def build(self, config: StudyConfig) -> TREE:
        pass  # end node has nothing to build

    def parse(self, path: Path) -> SUB_JSON:
        try:
            data: JSON = pd.read_csv(
                path,
                sep="\t",
                dtype=float,
                header=None,
            ).to_dict(orient="split")
            return data
        except EmptyDataError:
            return {}

    def format(self, data: SUB_JSON, path: Path) -> None:
        df = pd.DataFrame(**data)
        df.to_csv(path, sep="\t", header=False, index=False)

    def load(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
    ) -> SUB_JSON:
        return self.parse(self.config.path)

    def dump(self, data: JSON, url: Optional[List[str]] = None) -> None:
        self.format(data, self.config.path)

    def check_errors(
        self,
        data: JSON,
        url: Optional[List[str]] = None,
        raising: bool = False,
    ) -> List[str]:
        self._assert_url_end(url)

        errors = []
        if not self.config.path.exists():
            errors.append(
                f"Input Series Matrix f{self.config.path} not exists"
            )
        if self.nb_columns and len(data) != self.nb_columns:
            errors.append(
                f"{self.config.path}: Data was wrong size. expected {self.nb_columns} get {len(data)}"
            )
        return errors
