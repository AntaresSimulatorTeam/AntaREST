import logging
from pathlib import Path
from typing import Any, List, Optional, Union, cast

import pandas as pd
from pandas.errors import EmptyDataError

from antarest.core.model import JSON
from antarest.core.utils.utils import StopWatch
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency, MatrixNode

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
        default_empty: Optional[List[List[float]]] = None,
    ):
        super().__init__(context=context, config=config, freq=freq)
        self.nb_columns = nb_columns
        # Ensure that the matrix is a 2D matrix by setting it to [[]] if not provided
        self.default_empty = default_empty or [[]]

    def parse(
        self,
        file_path: Optional[Path] = None,
        tmp_dir: Any = None,
        return_dataframe: bool = False,
    ) -> Union[JSON, pd.DataFrame]:
        file_path = file_path or self.config.path

        stopwatch = StopWatch()

        link_path = self.get_link_path()
        if link_path.exists():
            link = link_path.read_text()
            matrix_json = self.context.resolver.resolve(link)
            matrix_json = cast(JSON, matrix_json)
            matrix: pd.DataFrame = pd.DataFrame(
                data=matrix_json["data"],
                columns=matrix_json["columns"],
                index=matrix_json["index"],
            )
        else:
            try:
                matrix = pd.read_csv(
                    file_path,
                    sep="\t",
                    dtype=float,
                    header=None,
                    float_precision="legacy",
                )
            except (FileNotFoundError, EmptyDataError):
                # Return an empty matrix if the CSV file is not found or empty.
                # Save the empty matrix as a CSV file for subsequent user modification.
                logger.warning(f"Empty file found when parsing {file_path}")
                df = pd.DataFrame(data=self.default_empty, dtype=float)
                df.to_csv(file_path, sep="\t", index=False, header=False)
                if return_dataframe:
                    return df
                return {
                    "data": df.values.tolist(),
                    "columns": df.columns.tolist(),
                    "index": df.index.tolist(),
                }

        stopwatch.log_elapsed(lambda x: logger.info(f"Matrix parsed in {x}s"))
        matrix.dropna(how="any", axis=1, inplace=True)
        if return_dataframe:
            return matrix

        data = cast(JSON, matrix.to_dict(orient="split"))
        stopwatch.log_elapsed(lambda x: logger.info(f"Matrix to dict in {x}s"))
        return data

    def check_errors(
        self,
        data: JSON,
        url: Optional[List[str]] = None,
        raising: bool = False,
    ) -> List[str]:
        self._assert_url_end(url)

        errors = []
        if not self.config.path.exists():
            errors.append(f"Input Series Matrix f{self.config.path} not exists")
        if self.nb_columns and len(data) != self.nb_columns:
            errors.append(f"{self.config.path}: Data was wrong size. expected {self.nb_columns} get {len(data)}")
        return errors
