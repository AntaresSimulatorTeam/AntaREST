from pathlib import Path
from typing import Optional, List, cast, Union

import numpy as np  # type: ignore
import pandas as pd  # type: ignore

from antarest.common.custom_types import JSON, SUB_JSON
from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.lazy_node import LazyNode
from antarest.storage.repository.filesystem.matrix.date_serializer import (
    IDateMatrixSerializer,
)
from antarest.storage.repository.filesystem.matrix.head_writer import (
    HeadWriter,
)
from antarest.storage.repository.filesystem.context import ContextServer
from antarest.storage.repository.filesystem.matrix.matrix import MatrixNode


class OutputSeriesMatrix(MatrixNode):
    """
    Generic node to handle output matrix behavior.
    Node needs a DateSerializer and a HeadWriter to work
    """

    def __init__(
        self,
        context: ContextServer,
        config: StudyConfig,
        date_serializer: IDateMatrixSerializer,
        head_writer: HeadWriter,
        freq: str,
    ):
        super().__init__(context=context, config=config, freq=freq)
        self.date_serializer = date_serializer
        self.head_writer = head_writer

    def build(self, config: StudyConfig) -> TREE:
        pass  # End of tree

    def load(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
    ) -> JSON:

        df = pd.read_csv(
            self.config.path, sep="\t", skiprows=4, na_values="N/A"
        )

        date, body = self.date_serializer.extract_date(df)

        header = body.iloc[:2]
        header.fillna("", inplace=True)
        header = np.array(
            [header.columns, header.iloc[0], header.iloc[1]]
        ).tolist()

        matrix = body.iloc[2:].astype(float)
        matrix = matrix.where(pd.notna(matrix), None)
        matrix.index = date
        matrix.columns = header

        return cast(JSON, matrix.to_dict(orient="split"))

    def _dump_json(self, data: JSON) -> None:
        df = pd.DataFrame(**data)

        headers = pd.DataFrame(df.columns.values.tolist()).T
        matrix = pd.concat([headers, pd.DataFrame(df.values)], axis=0)

        time = self.date_serializer.build_date(df.index)
        matrix.index = time.index

        matrix = pd.concat([time, matrix], axis=1)

        head = self.head_writer.build(var=df.columns.size, end=df.index.size)
        self.config.path.write_text(head)

        matrix.to_csv(
            open(self.config.path, "a", newline="\n"),
            sep="\t",
            index=False,
            header=False,
            line_terminator="\n",
        )

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
                f"Output Series Matrix f{self.config.path} not exists"
            )
        return errors
