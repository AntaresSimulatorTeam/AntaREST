import io
import logging
from pathlib import Path
from typing import Any, List, Optional, Union, cast

import pandas as pd
from pandas import DataFrame

from antarest.core.exceptions import ChildNotFoundError, MustNotModifyOutputException
from antarest.core.model import JSON
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.lazy_node import LazyNode
from antarest.study.storage.rawstudy.model.filesystem.matrix.date_serializer import (
    FactoryDateSerializer,
    IDateMatrixSerializer,
    rename_unnamed,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.head_writer import (
    AreaHeadWriter,
    HeadWriter,
    LinkHeadWriter,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency

logger = logging.getLogger(__name__)


class OutputSeriesMatrix(LazyNode[Union[bytes, JSON], Union[bytes, JSON], JSON]):
    """
    Generic node to handle output matrix behavior.
    Node needs a DateSerializer and a HeadWriter to work
    """

    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        freq: MatrixFrequency,
        date_serializer: IDateMatrixSerializer,
        head_writer: HeadWriter,
    ):
        super().__init__(context=context, config=config)
        self.date_serializer = date_serializer
        self.head_writer = head_writer
        self.freq = freq

    def get_lazy_content(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
    ) -> str:
        # noinspection SpellCheckingInspection
        return f"matrixfile://{self.config.path.name}"

    def parse_dataframe(
        self,
        file_path: Optional[Path] = None,
        tmp_dir: Any = None,
    ) -> DataFrame:
        file_path = file_path or self.config.path
        try:
            df = pd.read_csv(
                file_path,
                sep="\t",
                skiprows=4,
                header=[0, 1, 2],
                na_values="N/A",
                float_precision="legacy",
            )
        except FileNotFoundError as e:
            # Raise 404 'Not Found' if the TSV file is not found
            logger.warning(f"Matrix file'{file_path}' not found")
            study_id = self.config.study_id
            relpath = file_path.relative_to(self.config.study_path).as_posix()
            raise ChildNotFoundError(f"File '{relpath}' not found in the study '{study_id}'") from e

        if tmp_dir:
            tmp_dir.cleanup()

        date, body = self.date_serializer.extract_date(df)

        matrix = rename_unnamed(body).astype(float)
        matrix = matrix.where(pd.notna(matrix), None)
        matrix.index = date
        matrix.columns = body.columns
        return matrix

    def parse(self, file_path: Path, tmp_dir: Any, format: Optional[str] = None) -> Union[JSON, bytes]:
        matrix = self.parse_dataframe(file_path, tmp_dir)
        if format == "json":
            return cast(JSON, matrix.to_dict(orient="split"))
        else:
            with io.BytesIO() as buffer:
                matrix.columns = matrix.columns.map(str)
                matrix.reset_index(inplace=True)
                matrix.rename(columns={matrix.columns[0]: "Index"}, inplace=True)
                matrix.to_feather(buffer, compression="uncompressed")
                return buffer.getvalue()

    def check_errors(
        self,
        data: JSON,
        url: Optional[List[str]] = None,
        raising: bool = False,
    ) -> List[str]:
        self._assert_url_end(url)

        errors = []
        if not self.config.path.exists():
            errors.append(f"Output Series Matrix f{self.config.path} not exists")
        return errors

    def load(
        self, url: Optional[List[str]] = None, depth: int = -1, expanded: bool = False, format: Optional[str] = None
    ) -> Union[bytes, JSON]:
        try:
            file_path, tmp_dir = self._get_real_file_path()
            if not format:
                if file_path.exists():
                    file_content = file_path.read_bytes()
                    if tmp_dir:
                        tmp_dir.cleanup()
                    return file_content

                logger.warning(f"Missing file {self.config.path}")
                if tmp_dir:
                    tmp_dir.cleanup()
                return b""

            if not file_path.exists():
                raise FileNotFoundError(file_path)
            return self.parse(file_path, tmp_dir, format)
        except FileNotFoundError as e:
            raise ChildNotFoundError(
                f"Output file '{self.config.path.name}' not found in study {self.config.study_id}"
            ) from e

    def dump(self, data: Union[bytes, JSON], url: Optional[List[str]] = None) -> None:
        raise MustNotModifyOutputException(self.config.path.name)

    def normalize(self) -> None:
        pass  # no external store in this node

    def denormalize(self) -> None:
        pass  # no external store in this node


class LinkOutputSeriesMatrix(OutputSeriesMatrix):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        freq: MatrixFrequency,
        src: str,
        dest: str,
    ):
        super(LinkOutputSeriesMatrix, self).__init__(
            context=context,
            config=config,
            freq=freq,
            date_serializer=FactoryDateSerializer.create(freq, src),
            head_writer=LinkHeadWriter(src, dest, freq),
        )


class AreaOutputSeriesMatrix(OutputSeriesMatrix):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        freq: MatrixFrequency,
        area: str,
    ):
        super(AreaOutputSeriesMatrix, self).__init__(
            context,
            config=config,
            freq=freq,
            date_serializer=FactoryDateSerializer.create(freq, area),
            head_writer=AreaHeadWriter(area, config.path.name[:2], freq),
        )


class BindingConstraintOutputSeriesMatrix(OutputSeriesMatrix):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        freq: MatrixFrequency,
    ):
        super(BindingConstraintOutputSeriesMatrix, self).__init__(
            context,
            config=config,
            freq=freq,
            date_serializer=FactoryDateSerializer.create(freq, "system"),
            head_writer=AreaHeadWriter("system", config.path.name[:2], freq),
        )
