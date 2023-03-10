import uuid
from pathlib import Path
from unittest.mock import Mock

import pytest

from antarest.matrixstore.service import ISimpleMatrixService
from antarest.matrixstore.uri_resolver_service import UriResolverService
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.constants import (
    default_scenario_monthly,
    default_scenario_hourly,
    default_scenario_daily,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import (
    InputSeriesMatrix,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import (
    MatrixFrequency,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.hydro.series.area import (
    area,
)


AFTER_650 = {
    "mod": {
        "freq": MatrixFrequency.DAILY,
        "default_empty": default_scenario_daily,
    },
    "ror": {
        "freq": MatrixFrequency.HOURLY,
        "default_empty": default_scenario_hourly,
    },
}

BEFORE_650 = {
    "mod": {
        "freq": MatrixFrequency.MONTHLY,
        "default_empty": default_scenario_monthly,
    },
    "ror": {
        "freq": MatrixFrequency.HOURLY,
        "default_empty": default_scenario_hourly,
    },
}


class TestInputHydroSeriesArea:
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
            areas={},
        )

        node = area.InputHydroSeriesArea(
            context=context,
            config=config,
            children_glob_exceptions=None,
        )
        actual = node.build()

        # check the result
        value: InputSeriesMatrix
        actual_obj = {
            key: {
                "freq": value.freq,
                "default_empty": value.default_empty,
            }
            for key, value in actual.items()
        }
        assert actual_obj == expected
