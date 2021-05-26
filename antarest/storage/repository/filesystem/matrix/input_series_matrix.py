import os
import shutil
from pathlib import Path

import pandas as pd  # type: ignore

from typing import Optional, List

from pandas.errors import EmptyDataError  # type: ignore

from antarest.common.custom_types import JSON, SUB_JSON
from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.inode import INode, TREE


class InputSeriesMatrix(INode[SUB_JSON, JSON, JSON]):
    def __init__(self, config: StudyConfig, nb_columns: Optional[int] = None):
        self.config = config
        self.nb_columns = nb_columns

    def build(self, config: StudyConfig) -> TREE:
        pass  # end node has nothing to build

    def get(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
    ) -> SUB_JSON:
        self._assert_url(url)
        if expanded:
            return f"file://{self.config.path.absolute()}"

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

    def save(self, data: JSON, url: Optional[List[str]] = None) -> None:
        self._assert_url(url)

        if isinstance(data, str) and "file://" in data:
            src = Path(data[len("file://") :])
            if src != self.config.path:
                shutil.copyfile(src, self.config.path)
            return None

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
                f"Data was wrong size. expected {self.nb_columns} get {len(data)}"
            )
        return errors
