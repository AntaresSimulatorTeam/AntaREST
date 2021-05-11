from abc import ABC

import pandas as pd  # type: ignore

from typing import Optional, List, cast

from antarest.common.custom_types import JSON
from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.inode import INode, TREE
from antarest.storage.repository.filesystem.matrix.date_serializer import (
    IDateMatrixSerializer,
)
from antarest.storage.repository.filesystem.matrix.head_writer import (
    HeadWriter,
)


class OutputSeriesMatrix(INode[JSON, JSON, JSON]):
    def __init__(
        self,
        config: StudyConfig,
        date_serializer: IDateMatrixSerializer,
        head_writer: HeadWriter,
    ):
        self.config = config
        self.date_serializer = date_serializer
        self.head_writer = head_writer

    def build(self, config: StudyConfig) -> TREE:
        pass  # End of tree

    def get(self, url: Optional[List[str]] = None, depth: int = -1) -> JSON:
        df = pd.read_csv(
            self.config.path, sep="\t", skiprows=4, na_values="N/A"
        )

        date, body = self.date_serializer.extract_date(df)

        header = body.iloc[:2]
        header.fillna("", inplace=True)
        header = (
            header.columns + "::" + header.iloc[0] + "::" + header.iloc[1]
        ).to_list()

        matrix = body.iloc[2:].astype(float)
        matrix.index = date
        matrix.columns = header

        return cast(JSON, matrix.to_dict())

    def save(self, data: JSON, url: Optional[List[str]] = None) -> None:
        df = pd.DataFrame(data)

        headers = df.columns.map(lambda x: x.split("::"))
        headers = pd.DataFrame(headers.values.tolist()).T
        matrix = pd.concat([headers, pd.DataFrame(df.values)], axis=0)

        time = self.date_serializer.build_date(df.index)
        matrix.index = time.index
        matrix = pd.concat([time, matrix], axis=1)

        head = self.head_writer.build(var=df.columns.size, end=df.index.size)
        self.config.path.write_text(head)

        matrix.to_csv(
            open(self.config.path, "a"), sep="\t", index=False, header=False
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
                f"Output Series Matrix f{self.config.path} not exists"
            )
        return errors

    def _assert_url(self, url: Optional[List[str]] = None) -> None:
        url = url or []
        if len(url) > 0:
            raise ValueError(
                f"url should be fully resolved when arrives on {self.__class__.__name__}"
            )
