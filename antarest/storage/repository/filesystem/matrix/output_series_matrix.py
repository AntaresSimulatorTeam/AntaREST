from abc import ABC

import pandas as pd

from typing import Optional, List

from antarest.common.custom_types import JSON
from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.inode import INode, TREE
from antarest.storage.repository.filesystem.matrix.date_serializer import (
    IDateMatrixSerializer,
)


class OutputSeriesMatrix(INode[JSON, JSON, JSON]):
    def __init__(
        self, config: StudyConfig, date_serializer: IDateMatrixSerializer
    ):
        self.config = config
        self.date_serializer = date_serializer

    def build(self, config: StudyConfig) -> TREE:
        pass  # End of tree

    def get(self, url: Optional[List[str]] = None, depth: int = -1) -> JSON:
        df = pd.read_csv(self.config.path, sep="\t", skiprows=4)
        date, body = self.date_serializer.extract_date(df)

        header = body.iloc[:2]
        header = (
            header.columns
            + " - "
            + header.iloc[1]
            + " ("
            + header.iloc[0]
            + ")"
        ).to_list()

        matrix = body.iloc[2:].astype(float)
        matrix.index = date
        matrix.columns = header

        return matrix.to_dict()

    def save(self, data: JSON, url: Optional[List[str]] = None) -> None:
        pass

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
                f"Output Series Matrix f{self.config.path} not exists"
            )
        return errors

    def _assert_url(self, url: Optional[List[str]] = None) -> None:
        url = url or []
        if len(url) > 0:
            raise ValueError(
                f"url should be fully resolved when arrives on {self.__class__.__name__}"
            )
