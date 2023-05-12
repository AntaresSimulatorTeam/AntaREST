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
    BindingConstraintOutputSeriesMatrix,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.common import (
    binding_const,
)

# noinspection SpellCheckingInspection
NOMINAL_CASE = {
    "binding-constraints-annual": {"freq": MatrixFrequency.ANNUAL},
    "binding-constraints-daily": {"freq": MatrixFrequency.DAILY},
    "binding-constraints-hourly": {"freq": MatrixFrequency.HOURLY},
    "binding-constraints-monthly": {"freq": MatrixFrequency.MONTHLY},
    "binding-constraints-weekly": {"freq": MatrixFrequency.WEEKLY},
}


class TestOutputSimulationBindingConstraintItem:
    @pytest.mark.parametrize(
        "expected",
        [
            pytest.param(NOMINAL_CASE, id="nominal-case-True"),
        ],
    )
    def test_build_output_simulation_binding_constraint_item(
        self,
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

        node = binding_const.OutputSimulationBindingConstraintItem(
            context=context,
            config=config,
            children_glob_exceptions=None,
        )
        actual = node.build()

        # check the result
        value: BindingConstraintOutputSeriesMatrix
        actual_obj = {
            key: {"freq": value.freq} for key, value in actual.items()
        }
        assert actual_obj == expected
