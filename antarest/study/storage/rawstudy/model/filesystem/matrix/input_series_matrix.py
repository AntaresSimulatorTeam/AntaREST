import logging
from pathlib import Path
from typing import Any, List, Optional, Union, cast

import numpy as np
import pandas as pd

from antarest.core.model import JSON
from antarest.core.utils.utils import StopWatch
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import (
    MatrixFrequency,
    MatrixNode,
)
from numpy import typing as npt
from pandas.errors import EmptyDataError

logger = logging.getLogger(__name__)


class InputSeriesMatrix(MatrixNode):
    """
    Generic node to handle input matrix behavior
    """

    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        freq: MatrixFrequency = MatrixFrequency.HOURLY,
        nb_columns: Optional[int] = None,
        default_empty: Optional[npt.NDArray[np.float64]] = None,
    ):
        super().__init__(context=context, config=config, freq=freq)
        self.nb_columns = nb_columns
        if default_empty is None:
            # Ensure that the matrix is a 2D matrix
            self.default_empty = np.empty((1, 0), dtype=np.float64)
        else:
            # Clone the template value and make it writable
            self.default_empty = np.copy(default_empty)
            self.default_empty.flags.writeable = True

    def parse(
        self,
        file_path: Optional[Path] = None,
        tmp_dir: Any = None,
        return_dataframe: bool = False,
    ) -> Union[JSON, pd.DataFrame]:
        file_path = file_path or self.config.path
        try:
            # sourcery skip: extract-method
            stopwatch = StopWatch()
            if self.get_link_path().exists():
                link = self.get_link_path().read_text()
                matrix_json = self.context.resolver.resolve(link)
                matrix_json = cast(JSON, matrix_json)
                matrix: pd.DataFrame = pd.DataFrame(
                    data=matrix_json["data"],
                    columns=matrix_json["columns"],
                    index=matrix_json["index"],
                )
            else:
                matrix = pd.read_csv(
                    file_path,
                    sep="\t",
                    dtype=float,
                    header=None,
                    float_precision="legacy",
                )
            stopwatch.log_elapsed(
                lambda x: logger.info(f"Matrix parsed in {x}s")
            )
            matrix.dropna(how="any", axis=1, inplace=True)
            if return_dataframe:
                return matrix

            data = cast(JSON, matrix.to_dict(orient="split"))
            stopwatch.log_elapsed(
                lambda x: logger.info(f"Matrix to dict in {x}s")
            )

            return data
        except EmptyDataError:
            logger.warning(f"Empty file found when parsing {file_path}")
            matrix = pd.DataFrame(self.default_empty)
            return (
                matrix
                if return_dataframe
                else cast(JSON, matrix.to_dict(orient="split"))
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
                f"Input Series Matrix f{self.config.path} not exists"
            )
        if self.nb_columns and len(data) != self.nb_columns:
            errors.append(
                f"{self.config.path}: Data was wrong size. expected {self.nb_columns} get {len(data)}"
            )
        return errors
