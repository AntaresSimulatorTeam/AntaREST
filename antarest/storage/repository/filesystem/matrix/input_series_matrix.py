import pandas as pd

from typing import Optional, List

from antarest.common.custom_types import JSON
from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.inode import INode, TREE


class InputSeriesMatrix(INode[JSON, JSON, JSON]):
    def __init__(self, config: StudyConfig, nb_columns: Optional[int] = None):
        self.config = config
        self.nb_columns = nb_columns

    def build(self, config: StudyConfig) -> TREE:
        pass  # end node has nothing to build

    def get(self, url: Optional[List[str]] = None, depth: int = -1) -> JSON:
        self._assert_url(url)
        data: JSON = pd.read_csv(
            self.config.path, sep="\t", dtype=float, header=None
        ).to_dict()
        return data

    def save(self, data: JSON, url: Optional[List[str]] = None) -> None:
        self._assert_url(url)
        pd.DataFrame(data).to_csv(
            self.config.path, sep="\t", header=False, index=False
        )

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

    def _assert_url(self, url: Optional[List[str]] = None) -> None:
        url = url or []
        if len(url) > 0:
            raise ValueError(
                f"url should be fully resolved when arrives on {self.__class__.__name__}"
            )
