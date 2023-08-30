import uuid
from pathlib import Path
from unittest.mock import Mock

import pytest

from antarest.matrixstore.service import ISimpleMatrixService
from antarest.matrixstore.uri_resolver_service import UriResolverService
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency
from antarest.study.storage.rawstudy.model.filesystem.matrix.output_series_matrix import AreaOutputSeriesMatrix
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.common import area

# noinspection SpellCheckingInspection
MC_ALL_TRUE = {
    "details-annual": {"time_step": MatrixFrequency.ANNUAL},
    "details-daily": {"time_step": MatrixFrequency.DAILY},
    "details-hourly": {"time_step": MatrixFrequency.HOURLY},
    "details-monthly": {"time_step": MatrixFrequency.MONTHLY},
    "details-res-annual": {"time_step": MatrixFrequency.ANNUAL},
    "details-res-daily": {"time_step": MatrixFrequency.DAILY},
    "details-res-hourly": {"time_step": MatrixFrequency.HOURLY},
    "details-res-monthly": {"time_step": MatrixFrequency.MONTHLY},
    "details-res-weekly": {"time_step": MatrixFrequency.WEEKLY},
    "details-weekly": {"time_step": MatrixFrequency.WEEKLY},
    "id-annual": {"time_step": MatrixFrequency.ANNUAL},
    "id-daily": {"time_step": MatrixFrequency.DAILY},
    "id-hourly": {"time_step": MatrixFrequency.HOURLY},
    "id-monthly": {"time_step": MatrixFrequency.MONTHLY},
    "id-weekly": {"time_step": MatrixFrequency.WEEKLY},
    "values-annual": {"time_step": MatrixFrequency.ANNUAL},
    "values-daily": {"time_step": MatrixFrequency.DAILY},
    "values-hourly": {"time_step": MatrixFrequency.HOURLY},
    "values-monthly": {"time_step": MatrixFrequency.MONTHLY},
    "values-weekly": {"time_step": MatrixFrequency.WEEKLY},
}

# noinspection SpellCheckingInspection
MC_ALL_FALSE = {
    "details-annual": {"time_step": MatrixFrequency.ANNUAL},
    "details-daily": {"time_step": MatrixFrequency.DAILY},
    "details-hourly": {"time_step": MatrixFrequency.HOURLY},
    "details-monthly": {"time_step": MatrixFrequency.MONTHLY},
    "details-res-annual": {"time_step": MatrixFrequency.ANNUAL},
    "details-res-daily": {"time_step": MatrixFrequency.DAILY},
    "details-res-hourly": {"time_step": MatrixFrequency.HOURLY},
    "details-res-monthly": {"time_step": MatrixFrequency.MONTHLY},
    "details-res-weekly": {"time_step": MatrixFrequency.WEEKLY},
    "details-weekly": {"time_step": MatrixFrequency.WEEKLY},
    "values-annual": {"time_step": MatrixFrequency.ANNUAL},
    "values-daily": {"time_step": MatrixFrequency.DAILY},
    "values-hourly": {"time_step": MatrixFrequency.HOURLY},
    "values-monthly": {"time_step": MatrixFrequency.MONTHLY},
    "values-weekly": {"time_step": MatrixFrequency.WEEKLY},
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
        actual_obj = {key: {"time_step": value.freq} for key, value in actual.items()}
        assert actual_obj == expected

        new_config = FileStudyTreeConfig(
            study_path=Path("path/to/study"),
            path=Path("path/to/study"),
            study_id=study_id,
            version=860,  # will become a `str` in the future
            areas={},
        )

        new_node = area.OutputSimulationAreaItem(
            context=context,
            config=new_config,
            area="fr",
            mc_all=mc_all,
        )
        new_actual = new_node.build()
        # check the result
        actual_obj = {key: {"time_step": value.freq} for key, value in new_actual.items()}
        expected["details-STstorage-annual"] = {
            "time_step": MatrixFrequency.ANNUAL
        }
        expected["details-STstorage-daily"] = {
            "time_step": MatrixFrequency.DAILY
        }
        expected["details-STstorage-hourly"] = {
            "time_step": MatrixFrequency.HOURLY
        }
        expected["details-STstorage-monthly"] = {"time_step": MatrixFrequency.MONTHLY}
        expected["details-STstorage-weekly"] = {
            "time_step": MatrixFrequency.WEEKLY
        }

        assert actual_obj == expected
