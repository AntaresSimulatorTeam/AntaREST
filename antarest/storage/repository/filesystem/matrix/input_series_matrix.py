from typing import Optional, List

import pandas as pd  # type: ignore
from pandas.errors import EmptyDataError  # type: ignore

from antarest.common.custom_types import JSON, SUB_JSON
from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.lazy_node import LazyNode
from antarest.storage.repository.filesystem.context import ContextServer


class InputSeriesMatrix(LazyNode[SUB_JSON, JSON, JSON]):
    """
    Generic node to handle input matrix behavior
    """

    def __init__(
        self,
        context: ContextServer,
        config: StudyConfig,
        nb_columns: Optional[int] = None,
    ):
        super().__init__(url_prefix="matrix")
        self.context = context
        self.config = config
        self.nb_columns = nb_columns

    def build(self, config: StudyConfig) -> TREE:
        pass  # end node has nothing to build

    def load(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
    ) -> SUB_JSON:
        try:
            data: JSON = pd.read_csv(
                self.config.path,
                sep="\t",
                dtype=float,
                header=None,
            ).to_dict(orient="split")
            return data
        except EmptyDataError:
            return {}

    def dump(self, data: JSON, url: Optional[List[str]] = None) -> None:
        df = pd.DataFrame(**data)
        df.to_csv(self.config.path, sep="\t", header=False, index=False)

    def check_errors(
        self,
        data: JSON,
        url: Optional[List[str]] = None,
        raising: bool = False,
    ) -> List[str]:
        self._assert_url(url)

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
