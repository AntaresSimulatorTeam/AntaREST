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
from antarest.study.storage.rawstudy.model.filesystem.root.input.hydro.common.capacity import (
    capacity,
)


class TestInputHydroCommonCapacity:
    @pytest.mark.parametrize(
        "version, expected_keys",
        [
            pytest.param(
                0,
                {
                    "maxpower_en",
                    "maxpower_fr",
                    "reservoir_en",
                    "reservoir_fr",
                },
                id="before-650",
            ),
            pytest.param(
                650,
                {
                    "creditmodulations_en",
                    "creditmodulations_fr",
                    "inflowPattern_en",
                    "inflowPattern_fr",
                    "maxpower_en",
                    "maxpower_fr",
                    "reservoir_en",
                    "reservoir_fr",
                    "waterValues_en",
                    "waterValues_fr",
                },
                id="version-650",
            ),
        ],
    )
    def test_build_input_hydro_common_capacity(
        self,
        version: int,
        expected_keys: set,
    ):
        matrix = Mock(spec=ISimpleMatrixService)
        resolver = Mock(spec=UriResolverService)
        context = ContextServer(matrix=matrix, resolver=resolver)
        study_id = str(uuid.uuid4())
        config = FileStudyTreeConfig(
            study_path=Path("path/to/study"),
            path=Path("path/to/study"),
            study_id=study_id,
            version=version,
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
        # compare keys because we are lazy :-(
        assert set(actual) == expected_keys
