import logging
from pathlib import Path
from typing import List, Optional, Any, Union, cast

import pandas as pd  # type: ignore
from pandas.errors import EmptyDataError  # type: ignore

from antarest.core.model import JSON
from antarest.core.utils.utils import StopWatch
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import (
    MatrixNode,
)

logger = logging.getLogger(__name__)


class InputSeriesMatrix(MatrixNode):
    """
    Generic node to handle input matrix behavior
    """

    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        nb_columns: Optional[int] = None,
        freq: str = "hourly",
    ):
        super().__init__(context=context, config=config, freq=freq)
        self.nb_columns = nb_columns

    def parse(
        self,
        file_path: Optional[Path] = None,
        tmp_dir: Any = None,
        return_dataframe: bool = False,
    ) -> Union[JSON, pd.DataFrame]:
        file_path = file_path or self.config.path
        try:
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

            data: JSON = matrix.to_dict(orient="split")
            stopwatch.log_elapsed(
                lambda x: logger.info(f"Matrix to dict in {x}s")
            )

            return data
        except EmptyDataError:
            logger.warning(f"Empty file found when parsing {file_path}")
            return {}

    def _dump_json(self, data: JSON) -> None:
        df = pd.DataFrame(**data)
        if not df.empty:
            df.to_csv(
                self.config.path,
                sep="\t",
                header=False,
                index=False,
                float_format="%.6f",
            )
        else:
            self.config.path.write_bytes(b"")

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
