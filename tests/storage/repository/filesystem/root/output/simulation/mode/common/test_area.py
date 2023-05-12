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
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import (
    MatrixFrequency,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.output_series_matrix import (
    AreaOutputSeriesMatrix,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.common import (
    area,
)

# noinspection SpellCheckingInspection
MC_ALL_TRUE = {
    "details-annual": {"freq": MatrixFrequency.ANNUAL},
    "details-daily": {"freq": MatrixFrequency.DAILY},
    "details-hourly": {"freq": MatrixFrequency.HOURLY},
    "details-monthly": {"freq": MatrixFrequency.MONTHLY},
    "details-res-annual": {"freq": MatrixFrequency.ANNUAL},
    "details-res-daily": {"freq": MatrixFrequency.DAILY},
    "details-res-hourly": {"freq": MatrixFrequency.HOURLY},
    "details-res-monthly": {"freq": MatrixFrequency.MONTHLY},
    "details-res-weekly": {"freq": MatrixFrequency.WEEKLY},
    "details-weekly": {"freq": MatrixFrequency.WEEKLY},
    "id-annual": {"freq": MatrixFrequency.ANNUAL},
    "id-daily": {"freq": MatrixFrequency.DAILY},
    "id-hourly": {"freq": MatrixFrequency.HOURLY},
    "id-monthly": {"freq": MatrixFrequency.MONTHLY},
    "id-weekly": {"freq": MatrixFrequency.WEEKLY},
    "values-annual": {"freq": MatrixFrequency.ANNUAL},
    "values-daily": {"freq": MatrixFrequency.DAILY},
    "values-hourly": {"freq": MatrixFrequency.HOURLY},
    "values-monthly": {"freq": MatrixFrequency.MONTHLY},
    "values-weekly": {"freq": MatrixFrequency.WEEKLY},
}

# noinspection SpellCheckingInspection
MC_ALL_FALSE = {
    "details-annual": {"freq": MatrixFrequency.ANNUAL},
    "details-daily": {"freq": MatrixFrequency.DAILY},
    "details-hourly": {"freq": MatrixFrequency.HOURLY},
    "details-monthly": {"freq": MatrixFrequency.MONTHLY},
    "details-res-annual": {"freq": MatrixFrequency.ANNUAL},
    "details-res-daily": {"freq": MatrixFrequency.DAILY},
    "details-res-hourly": {"freq": MatrixFrequency.HOURLY},
    "details-res-monthly": {"freq": MatrixFrequency.MONTHLY},
    "details-res-weekly": {"freq": MatrixFrequency.WEEKLY},
    "details-weekly": {"freq": MatrixFrequency.WEEKLY},
    "values-annual": {"freq": MatrixFrequency.ANNUAL},
    "values-daily": {"freq": MatrixFrequency.DAILY},
    "values-hourly": {"freq": MatrixFrequency.HOURLY},
    "values-monthly": {"freq": MatrixFrequency.MONTHLY},
    "values-weekly": {"freq": MatrixFrequency.WEEKLY},
}


class TestOutputSimulationAreaItem:
    @pytest.mark.parametrize(
        "mc_all, expected",
        [
            pytest.param(True, MC_ALL_TRUE, id="mc-all-True"),
            pytest.param(False, MC_ALL_FALSE, id="mc-all-False"),
        ],
    )
    def test_build_output_simulation_area_item(
        self,
        mc_all: bool,
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
            version=850,  # will become a `str` in the future
            areas={},
        )

        node = area.OutputSimulationAreaItem(
            context=context,
            config=config,
            area="fr",
            mc_all=mc_all,
        )
        actual = node.build()

        # check the result
        value: AreaOutputSeriesMatrix
        actual_obj = {
            key: {"freq": value.freq} for key, value in actual.items()
        }
        assert actual_obj == expected
