import uuid
from pathlib import Path
from unittest.mock import Mock

import pytest

from antarest.matrixstore.service import ISimpleMatrixService
from antarest.matrixstore.uri_resolver_service import UriResolverService
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    Area,
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import (
    InputSeriesMatrix,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import (
    MatrixFrequency,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.hydro.common.capacity import (
    capacity,
)


# noinspection SpellCheckingInspection
BEFORE_650 = {
    # fmt: off
    "maxpower_en": {"default_empty": None, "freq": MatrixFrequency.HOURLY, "nb_columns": None},
    "maxpower_fr": {"default_empty": None, "freq": MatrixFrequency.HOURLY, "nb_columns": None},
    "reservoir_en": {"default_empty": None, "freq": MatrixFrequency.DAILY, "nb_columns": None},
    "reservoir_fr": {"default_empty": None, "freq": MatrixFrequency.DAILY, "nb_columns": None},
    # fmt: on
}

# noinspection SpellCheckingInspection
AFTER_650 = {
    # fmt: off
    "creditmodulations_en": {"default_empty": None, "freq": MatrixFrequency.HOURLY, "nb_columns": None},
    "creditmodulations_fr": {"default_empty": None, "freq": MatrixFrequency.HOURLY, "nb_columns": None},
    "inflowPattern_en": {"default_empty": None, "freq": MatrixFrequency.HOURLY, "nb_columns": None},
    "inflowPattern_fr": {"default_empty": None, "freq": MatrixFrequency.HOURLY, "nb_columns": None},
    "maxpower_en": {"default_empty": None, "freq": MatrixFrequency.HOURLY, "nb_columns": None},
    "maxpower_fr": {"default_empty": None, "freq": MatrixFrequency.HOURLY, "nb_columns": None},
    "reservoir_en": {"default_empty": None, "freq": MatrixFrequency.DAILY, "nb_columns": None},
    "reservoir_fr": {"default_empty": None, "freq": MatrixFrequency.DAILY, "nb_columns": None},
    "waterValues_en": {"default_empty": None, "freq": MatrixFrequency.DAILY, "nb_columns": None},
    "waterValues_fr": {"default_empty": None, "freq": MatrixFrequency.DAILY, "nb_columns": None},
    # fmt: on
}


class TestInputHydroCommonCapacity:
    @pytest.mark.parametrize(
        "version, expected",
        [
            pytest.param("000", BEFORE_650, id="before-650"),
            pytest.param("650", AFTER_650, id="after-650"),
        ],
    )
    def test_build_input_hydro_common_capacity(
        self,
        version: str,
        expected: dict,
    ):
        matrix = Mock(spec=ISimpleMatrixService)
        resolver = Mock(spec=UriResolverService)
        context = ContextServer(matrix=matrix, resolver=resolver)
        study_id = str(uuid.uuid4())
        config = FileStudyTreeConfig(
            study_path=Path("path/to/study"),
            path=Path("path/to/study"),
            study_id=study_id,
            version=int(version),  # will become a `str` in the future
            areas={
                name: Area(
                    name=name.upper(),
                    links={},
                    thermals=[],
                    renewables=[],
                    filters_synthesis=[],
                    filters_year=[],
                )
                for name in ["fr", "en"]
            },
        )

        node = capacity.InputHydroCommonCapacity(
            context=context,
            config=config,
            children_glob_exceptions=None,
        )
        actual = node.build()

        # check the result
        value: InputSeriesMatrix
        actual_obj = {
            key: {
                "default_empty": value.default_empty,
                "freq": value.freq,
                "nb_columns": value.nb_columns,
            }
            for key, value in actual.items()
        }
        assert actual_obj == expected
