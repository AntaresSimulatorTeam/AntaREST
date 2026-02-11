# Copyright (c) 2025, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.
import os
import shutil
import zipfile
from pathlib import Path
from unittest.mock import Mock

import pytest
from typing_extensions import override

from antarest.core.cache.business.local_chache import LocalCache
from antarest.core.exceptions import (
    OutputAlreadyArchived,
    OutputAlreadyExists,
    OutputAlreadyUnarchived,
    OutputNotFound,
    StudyNotFoundError,
)
from antarest.core.remote.remote_executor import IRemoteExecutor
from antarest.matrixstore.in_memory import InMemorySimpleMatrixService
from antarest.matrixstore.matrix_uri_mapper import MatrixUriMapperFactory, NormalizedMatrixUriMapper
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.model import StudySimResultDTO, StudySimSettingsDTO
from antarest.study.output.file_output_storage import FileStudyOutputs, IFileOutputsProvider, InStudyFileOutputStorage
from antarest.study.output.output_storage import BasicOutputMetadata
from antarest.study.storage.rawstudy.model.filesystem.config.files import build
from antarest.study.storage.rawstudy.model.filesystem.config.model import Mode, Simulation
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree


@pytest.fixture
def sta_mini_zip_path(project_path: Path) -> Path:
    return project_path / "examples/studies/STA-mini.zip"


class SimpleFileOutputsProvider(IFileOutputsProvider):
    """
    Maps study ID to outputs in <studies_dir> / <study_id> / output
    """

    def __init__(self, studies_dir: Path, matrix_service: ISimpleMatrixService):
        self._studies_dir = studies_dir
        self._matrix_service = matrix_service

    @override
    def get_outputs(self, study_id: str) -> FileStudyOutputs:
        if not (self._studies_dir / study_id).is_dir():
            raise StudyNotFoundError(f"Studies directory {self._studies_dir} not found.")
        return FileStudyOutputs(
            get_file_study=lambda: self._get_study(study_id),
            outputs_path=self._studies_dir / study_id / "output",
            study_workspace="default",
        )

    def _get_study(self, study_id: str) -> FileStudy:
        study_dir = self._studies_dir / study_id
        if not study_dir.is_dir():
            raise StudyNotFoundError(f"Study {study_id} not found.")
        config = build(study_dir, study_id)
        mapper_factory = MatrixUriMapperFactory(matrix_service=self._matrix_service)
        matrix_mapper = mapper_factory.create(NormalizedMatrixUriMapper.NORMALIZED)
        return FileStudy(config, FileStudyTree(matrix_mapper, config))


@pytest.fixture
def matrix_service() -> ISimpleMatrixService:
    return InMemorySimpleMatrixService()


@pytest.fixture
def file_output_storage(
    tmp_path: Path, sta_mini_zip_path: Path, matrix_service: ISimpleMatrixService
) -> InStudyFileOutputStorage:
    executor = Mock(spec=IRemoteExecutor)

    studies_dir = tmp_path / "studies"
    studies_dir.mkdir()

    with zipfile.ZipFile(sta_mini_zip_path, "r") as zf:
        outputs_filter = [
            n
            for n in zf.namelist()
            if n.startswith(
                "STA-mini/output/20201014-1427eco" or n.startswith("STA-mini/output/20201014-1422eco-hello")
            )
        ]
        zf.extractall(studies_dir, members=outputs_filter)

    outputs_provider = SimpleFileOutputsProvider(studies_dir, matrix_service)

    return InStudyFileOutputStorage(outputs_provider=outputs_provider, cache=LocalCache(), remote_executor=executor)


def test_file_output_storage(file_output_storage):
    assert file_output_storage.list_outputs("STA-mini") == [
        BasicOutputMetadata(id="20201014-1422eco-hello", in_study=True, archived=False),
        BasicOutputMetadata(id="20201014-1425eco-goodbye", in_study=True, archived=False),
        BasicOutputMetadata(id="20201014-1427eco", in_study=True, archived=False),
        BasicOutputMetadata(id="20201014-1430adq", in_study=True, archived=False),
        BasicOutputMetadata(id="20201014-1430adq-2", in_study=True, archived=True),
        BasicOutputMetadata(id="20241807-1540eco-extra-outputs", in_study=True, archived=False),
    ]

    with pytest.raises(StudyNotFoundError):
        file_output_storage.list_outputs("non-existent")

    assert file_output_storage.get_simulations("STA-mini") == {
        "20201014-1422eco-hello": Simulation(
            name="hello",
            date="20201014-1422",
            mode=Mode.ECONOMY,
            nbyears=1,
            synthesis=True,
            by_year=True,
            error=False,
            playlist=[1],
            archived=False,
            xpansion="",
        ),
        "20201014-1425eco-goodbye": Simulation(
            name="goodbye",
            date="20201014-1425",
            mode=Mode.ECONOMY,
            nbyears=2,
            synthesis=True,
            by_year=True,
            error=False,
            playlist=[1, 2],
            archived=False,
            xpansion="",
        ),
        "20201014-1427eco": Simulation(
            name="",
            date="20201014-1427",
            mode=Mode.ECONOMY,
            nbyears=1,
            synthesis=True,
            by_year=False,
            error=False,
            playlist=[1],
            archived=False,
            xpansion="",
        ),
        "20201014-1430adq": Simulation(
            name="",
            date="20201014-1430",
            mode=Mode.ADEQUACY,
            nbyears=1,
            synthesis=True,
            by_year=False,
            error=False,
            playlist=[1],
            archived=False,
            xpansion="",
        ),
        "20201014-1430adq-2": Simulation(
            name="2",
            date="20201014-1430",
            mode=Mode.ADEQUACY,
            nbyears=1,
            synthesis=True,
            by_year=False,
            error=False,
            playlist=[1],
            archived=True,
            xpansion="",
        ),
        "20241807-1540eco-extra-outputs": Simulation(
            name="extra-outputs",
            date="20241807-1540",
            mode=Mode.ECONOMY,
            nbyears=1,
            synthesis=True,
            by_year=True,
            error=False,
            playlist=[],
            archived=False,
            xpansion="",
        ),
    }

    with pytest.raises(StudyNotFoundError):
        file_output_storage.get_simulations("non-existent")

    assert file_output_storage.get_study_sim_result("STA-mini") == [
        StudySimResultDTO(
            name="20201014-1422eco-hello",
            type="Economy",
            settings=StudySimSettingsDTO(
                general={
                    "mode": "Economy",
                    "horizon": 2030,
                    "nbyears": 1,
                    "simulation.start": 1,
                    "simulation.end": 7,
                    "january.1st": "Monday",
                    "first-month-in-year": "january",
                    "first.weekday": "Monday",
                    "leapyear": False,
                    "year-by-year": True,
                    "derated": False,
                    "custom-ts-numbers": True,
                    "user-playlist": True,
                    "filtering": True,
                    "active-rules-scenario": "default ruleset",
                    "generate": "",
                    "nbtimeseriesload": 1,
                    "nbtimeserieshydro": 1,
                    "nbtimeserieswind": 1,
                    "nbtimeseriesthermal": 1,
                    "nbtimeseriessolar": 1,
                    "refreshtimeseries": "thermal",
                    "intra-modal": "",
                    "inter-modal": "",
                    "refreshintervalload": 100,
                    "refreshintervalhydro": 100,
                    "refreshintervalwind": 100,
                    "refreshintervalthermal": 1,
                    "refreshintervalsolar": 100,
                    "readonly": False,
                },
                input={"import": "thermal"},
                output={"synthesis": True, "storenewset": True, "archives": ""},
                optimization={
                    "simplex-range": "week",
                    "transmission-capacities": True,
                    "link-type": "local",
                    "include-constraints": True,
                    "include-hurdlecosts": True,
                    "include-tc-minstablepower": True,
                    "include-tc-min-ud-time": True,
                    "include-dayahead": True,
                    "include-strategicreserve": True,
                    "include-spinningreserve": True,
                    "include-primaryreserve": True,
                    "include-exportmps": False,
                },
                otherPreferences={
                    "initial-reservoir-levels": "cold start",
                    "power-fluctuations": "free modulations",
                    "shedding-strategy": "share margins",
                    "shedding-policy": "shave peaks",
                    "unit-commitment-mode": "fast",
                    "number-of-cores-mode": "maximum",
                    "day-ahead-reserve-management": "global",
                },
                advancedParameters={"accuracy-on-correlation": "", "adequacy-block-size": 100},
                seedsMersenneTwister={
                    "seed-tsgen-wind": 5489,
                    "seed-tsgen-load": 1005489,
                    "seed-tsgen-hydro": 2005489,
                    "seed-tsgen-thermal": 3005489,
                    "seed-tsgen-solar": 4005489,
                    "seed-tsnumbers": 5005489,
                    "seed-unsupplied-energy-costs": 6005489,
                    "seed-spilled-energy-costs": 7005489,
                    "seed-thermal-costs": 8005489,
                    "seed-hydro-costs": 9005489,
                    "seed-initial-reservoir-levels": 10005489,
                },
                playlist=[1],
            ),
            completionDate="",
            status="",
            archived=False,
        ),
        StudySimResultDTO(
            name="20201014-1425eco-goodbye",
            type="Economy",
            settings=StudySimSettingsDTO(
                general={
                    "mode": "Economy",
                    "horizon": 2030,
                    "nbyears": 2,
                    "simulation.start": 1,
                    "simulation.end": 14,
                    "january.1st": "Monday",
                    "first-month-in-year": "january",
                    "first.weekday": "Monday",
                    "leapyear": False,
                    "year-by-year": True,
                    "derated": False,
                    "custom-ts-numbers": True,
                    "user-playlist": True,
                    "filtering": True,
                    "active-rules-scenario": "default ruleset",
                    "generate": "",
                    "nbtimeseriesload": 1,
                    "nbtimeserieshydro": 1,
                    "nbtimeserieswind": 1,
                    "nbtimeseriesthermal": 1,
                    "nbtimeseriessolar": 1,
                    "refreshtimeseries": "thermal",
                    "intra-modal": "",
                    "inter-modal": "",
                    "refreshintervalload": 100,
                    "refreshintervalhydro": 100,
                    "refreshintervalwind": 100,
                    "refreshintervalthermal": 1,
                    "refreshintervalsolar": 100,
                    "readonly": False,
                },
                input={"import": "thermal"},
                output={"synthesis": True, "storenewset": True, "archives": ""},
                optimization={
                    "simplex-range": "week",
                    "transmission-capacities": True,
                    "link-type": "local",
                    "include-constraints": True,
                    "include-hurdlecosts": True,
                    "include-tc-minstablepower": True,
                    "include-tc-min-ud-time": True,
                    "include-dayahead": True,
                    "include-strategicreserve": True,
                    "include-spinningreserve": True,
                    "include-primaryreserve": True,
                    "include-exportmps": False,
                },
                otherPreferences={
                    "initial-reservoir-levels": "cold start",
                    "power-fluctuations": "free modulations",
                    "shedding-strategy": "share margins",
                    "shedding-policy": "shave peaks",
                    "unit-commitment-mode": "fast",
                    "number-of-cores-mode": "maximum",
                    "day-ahead-reserve-management": "global",
                },
                advancedParameters={"accuracy-on-correlation": "", "adequacy-block-size": 100},
                seedsMersenneTwister={
                    "seed-tsgen-wind": 5489,
                    "seed-tsgen-load": 1005489,
                    "seed-tsgen-hydro": 2005489,
                    "seed-tsgen-thermal": 3005489,
                    "seed-tsgen-solar": 4005489,
                    "seed-tsnumbers": 5005489,
                    "seed-unsupplied-energy-costs": 6005489,
                    "seed-spilled-energy-costs": 7005489,
                    "seed-thermal-costs": 8005489,
                    "seed-hydro-costs": 9005489,
                    "seed-initial-reservoir-levels": 10005489,
                },
                playlist=[1, 2],
            ),
            completionDate="",
            status="",
            archived=False,
        ),
        StudySimResultDTO(
            name="20201014-1427eco",
            type="Economy",
            settings=StudySimSettingsDTO(
                general={
                    "mode": "Economy",
                    "horizon": 2030,
                    "nbyears": 1,
                    "simulation.start": 1,
                    "simulation.end": 7,
                    "january.1st": "Monday",
                    "first-month-in-year": "january",
                    "first.weekday": "Monday",
                    "leapyear": False,
                    "year-by-year": False,
                    "derated": False,
                    "custom-ts-numbers": True,
                    "user-playlist": True,
                    "filtering": True,
                    "active-rules-scenario": "default ruleset",
                    "generate": "",
                    "nbtimeseriesload": 1,
                    "nbtimeserieshydro": 1,
                    "nbtimeserieswind": 1,
                    "nbtimeseriesthermal": 1,
                    "nbtimeseriessolar": 1,
                    "refreshtimeseries": "thermal",
                    "intra-modal": "",
                    "inter-modal": "",
                    "refreshintervalload": 100,
                    "refreshintervalhydro": 100,
                    "refreshintervalwind": 100,
                    "refreshintervalthermal": 1,
                    "refreshintervalsolar": 100,
                    "readonly": False,
                },
                input={"import": "thermal"},
                output={"synthesis": True, "storenewset": True, "archives": ""},
                optimization={
                    "simplex-range": "week",
                    "transmission-capacities": True,
                    "link-type": "local",
                    "include-constraints": True,
                    "include-hurdlecosts": True,
                    "include-tc-minstablepower": True,
                    "include-tc-min-ud-time": True,
                    "include-dayahead": True,
                    "include-strategicreserve": True,
                    "include-spinningreserve": True,
                    "include-primaryreserve": True,
                    "include-exportmps": False,
                },
                otherPreferences={
                    "initial-reservoir-levels": "cold start",
                    "power-fluctuations": "free modulations",
                    "shedding-strategy": "share margins",
                    "shedding-policy": "shave peaks",
                    "unit-commitment-mode": "fast",
                    "number-of-cores-mode": "maximum",
                    "day-ahead-reserve-management": "global",
                },
                advancedParameters={"accuracy-on-correlation": "", "adequacy-block-size": 100},
                seedsMersenneTwister={
                    "seed-tsgen-wind": 5489,
                    "seed-tsgen-load": 1005489,
                    "seed-tsgen-hydro": 2005489,
                    "seed-tsgen-thermal": 3005489,
                    "seed-tsgen-solar": 4005489,
                    "seed-tsnumbers": 5005489,
                    "seed-unsupplied-energy-costs": 6005489,
                    "seed-spilled-energy-costs": 7005489,
                    "seed-thermal-costs": 8005489,
                    "seed-hydro-costs": 9005489,
                    "seed-initial-reservoir-levels": 10005489,
                },
                playlist=[1],
            ),
            completionDate="",
            status="",
            archived=False,
        ),
        StudySimResultDTO(
            name="20201014-1430adq",
            type="Adequacy",
            settings=StudySimSettingsDTO(
                general={
                    "mode": "Adequacy",
                    "horizon": 2030,
                    "nbyears": 1,
                    "simulation.start": 1,
                    "simulation.end": 7,
                    "january.1st": "Monday",
                    "first-month-in-year": "january",
                    "first.weekday": "Monday",
                    "leapyear": False,
                    "year-by-year": False,
                    "derated": False,
                    "custom-ts-numbers": True,
                    "user-playlist": True,
                    "filtering": True,
                    "active-rules-scenario": "default ruleset",
                    "generate": "",
                    "nbtimeseriesload": 1,
                    "nbtimeserieshydro": 1,
                    "nbtimeserieswind": 1,
                    "nbtimeseriesthermal": 1,
                    "nbtimeseriessolar": 1,
                    "refreshtimeseries": "thermal",
                    "intra-modal": "",
                    "inter-modal": "",
                    "refreshintervalload": 100,
                    "refreshintervalhydro": 100,
                    "refreshintervalwind": 100,
                    "refreshintervalthermal": 1,
                    "refreshintervalsolar": 100,
                    "readonly": False,
                },
                input={"import": "thermal"},
                output={"synthesis": True, "storenewset": True, "archives": ""},
                optimization={
                    "simplex-range": "week",
                    "transmission-capacities": True,
                    "link-type": "local",
                    "include-constraints": True,
                    "include-hurdlecosts": True,
                    "include-tc-minstablepower": True,
                    "include-tc-min-ud-time": True,
                    "include-dayahead": True,
                    "include-strategicreserve": True,
                    "include-spinningreserve": True,
                    "include-primaryreserve": True,
                    "include-exportmps": False,
                },
                otherPreferences={
                    "initial-reservoir-levels": "cold start",
                    "power-fluctuations": "free modulations",
                    "shedding-strategy": "share margins",
                    "shedding-policy": "shave peaks",
                    "unit-commitment-mode": "fast",
                    "number-of-cores-mode": "maximum",
                    "day-ahead-reserve-management": "global",
                },
                advancedParameters={"accuracy-on-correlation": "", "adequacy-block-size": 100},
                seedsMersenneTwister={
                    "seed-tsgen-wind": 5489,
                    "seed-tsgen-load": 1005489,
                    "seed-tsgen-hydro": 2005489,
                    "seed-tsgen-thermal": 3005489,
                    "seed-tsgen-solar": 4005489,
                    "seed-tsnumbers": 5005489,
                    "seed-unsupplied-energy-costs": 6005489,
                    "seed-spilled-energy-costs": 7005489,
                    "seed-thermal-costs": 8005489,
                    "seed-hydro-costs": 9005489,
                    "seed-initial-reservoir-levels": 10005489,
                },
                playlist=[1],
            ),
            completionDate="",
            status="",
            archived=False,
        ),
        StudySimResultDTO(
            name="20201014-1430adq-2",
            type="Adequacy",
            settings=StudySimSettingsDTO(
                general={
                    "mode": "Adequacy",
                    "horizon": 2030,
                    "nbyears": 1,
                    "simulation.start": 1,
                    "simulation.end": 7,
                    "january.1st": "Monday",
                    "first-month-in-year": "january",
                    "first.weekday": "Monday",
                    "leapyear": False,
                    "year-by-year": False,
                    "derated": False,
                    "custom-ts-numbers": True,
                    "user-playlist": True,
                    "filtering": True,
                    "active-rules-scenario": "default ruleset",
                    "generate": "",
                    "nbtimeseriesload": 1,
                    "nbtimeserieshydro": 1,
                    "nbtimeserieswind": 1,
                    "nbtimeseriesthermal": 1,
                    "nbtimeseriessolar": 1,
                    "refreshtimeseries": "thermal",
                    "intra-modal": "",
                    "inter-modal": "",
                    "refreshintervalload": 100,
                    "refreshintervalhydro": 100,
                    "refreshintervalwind": 100,
                    "refreshintervalthermal": 1,
                    "refreshintervalsolar": 100,
                    "readonly": False,
                },
                input={"import": "thermal"},
                output={"synthesis": True, "storenewset": True, "archives": ""},
                optimization={
                    "simplex-range": "week",
                    "transmission-capacities": True,
                    "link-type": "local",
                    "include-constraints": True,
                    "include-hurdlecosts": True,
                    "include-tc-minstablepower": True,
                    "include-tc-min-ud-time": True,
                    "include-dayahead": True,
                    "include-strategicreserve": True,
                    "include-spinningreserve": True,
                    "include-primaryreserve": True,
                    "include-exportmps": False,
                },
                otherPreferences={
                    "initial-reservoir-levels": "cold start",
                    "power-fluctuations": "free modulations",
                    "shedding-strategy": "share margins",
                    "shedding-policy": "shave peaks",
                    "unit-commitment-mode": "fast",
                    "number-of-cores-mode": "maximum",
                    "day-ahead-reserve-management": "global",
                },
                advancedParameters={"accuracy-on-correlation": "", "adequacy-block-size": 100},
                seedsMersenneTwister={
                    "seed-tsgen-wind": 5489,
                    "seed-tsgen-load": 1005489,
                    "seed-tsgen-hydro": 2005489,
                    "seed-tsgen-thermal": 3005489,
                    "seed-tsgen-solar": 4005489,
                    "seed-tsnumbers": 5005489,
                    "seed-unsupplied-energy-costs": 6005489,
                    "seed-spilled-energy-costs": 7005489,
                    "seed-thermal-costs": 8005489,
                    "seed-hydro-costs": 9005489,
                    "seed-initial-reservoir-levels": 10005489,
                },
                playlist=[1],
            ),
            completionDate="",
            status="",
            archived=True,
        ),
        StudySimResultDTO(
            name="20241807-1540eco-extra-outputs",
            type="Economy",
            settings=StudySimSettingsDTO(
                general={
                    "mode": "Economy",
                    "horizon": "",
                    "nbyears": 1,
                    "simulation.start": 1,
                    "simulation.end": 365,
                    "january.1st": "Monday",
                    "first-month-in-year": "january",
                    "first.weekday": "Monday",
                    "leapyear": False,
                    "year-by-year": True,
                    "derated": False,
                    "custom-scenario": False,
                    "user-playlist": False,
                    "thematic-trimming": True,
                    "geographic-trimming": False,
                    "generate": "",
                    "nbtimeseriesload": 1,
                    "nbtimeserieshydro": 1,
                    "nbtimeserieswind": 1,
                    "nbtimeseriesthermal": 1,
                    "nbtimeseriessolar": 1,
                    "refreshtimeseries": "",
                    "intra-modal": "",
                    "inter-modal": "",
                    "refreshintervalload": 100,
                    "refreshintervalhydro": 100,
                    "refreshintervalwind": 100,
                    "refreshintervalthermal": 100,
                    "refreshintervalsolar": 100,
                    "readonly": False,
                },
                input={"import": ""},
                output={"synthesis": True, "storenewset": False, "archives": ""},
                optimization={
                    "simplex-range": "week",
                    "transmission-capacities": "local-values",
                    "link-type": "local",
                    "include-constraints": True,
                    "include-hurdlecosts": True,
                    "include-tc-minstablepower": True,
                    "include-tc-min-ud-time": True,
                    "include-dayahead": True,
                    "include-strategicreserve": True,
                    "include-spinningreserve": True,
                    "include-primaryreserve": True,
                    "include-exportmps": False,
                    "include-exportstructure": False,
                    "include-unfeasible-problem-behavior": "error-verbose",
                },
                otherPreferences={
                    "initial-reservoir-levels": "cold start",
                    "hydro-heuristic-policy": "accommodate rule curves",
                    "hydro-pricing-mode": "fast",
                    "power-fluctuations": "free modulations",
                    "shedding-strategy": "share margins",
                    "shedding-policy": "shave peaks",
                    "unit-commitment-mode": "fast",
                    "number-of-cores-mode": "medium",
                    "renewable-generation-modelling": "clusters",
                    "day-ahead-reserve-management": "global",
                },
                advancedParameters={"accuracy-on-correlation": "", "adequacy-block-size": 100},
                seedsMersenneTwister={
                    "seed-tsgen-wind": 5489,
                    "seed-tsgen-load": 1005489,
                    "seed-tsgen-hydro": 2005489,
                    "seed-tsgen-thermal": 3005489,
                    "seed-tsgen-solar": 4005489,
                    "seed-tsnumbers": 5005489,
                    "seed-unsupplied-energy-costs": 6005489,
                    "seed-spilled-energy-costs": 7005489,
                    "seed-thermal-costs": 8005489,
                    "seed-hydro-costs": 9005489,
                    "seed-initial-reservoir-levels": 10005489,
                },
                playlist=[],
            ),
            completionDate="",
            status="",
            archived=False,
        ),
    ]

    with pytest.raises(StudyNotFoundError):
        file_output_storage.get_study_sim_result("unknown")


def test_output_deletion(file_output_storage: InStudyFileOutputStorage) -> None:
    outputs = file_output_storage.list_outputs("STA-mini")
    assert len(outputs) == 6
    assert "20201014-1427eco" in [o.id for o in outputs]
    file_output_storage.delete_output("STA-mini", "20201014-1427eco")

    outputs = file_output_storage.list_outputs("STA-mini")
    assert len(outputs) == 5
    assert "20201014-1427eco" not in [o.id for o in outputs]

    # TODO: could add a check on the directory on disk
    with pytest.raises(StudyNotFoundError):
        file_output_storage.delete_output("non-existent", "20201014-1427eco")

    with pytest.raises(OutputNotFound):
        file_output_storage.delete_output("STA-mini", "non-existent")

    file_output_storage.archive_study_output("STA-mini", "20201014-1422eco-hello")
    assert file_output_storage.is_output_archived("STA-mini", "20201014-1422eco-hello")
    assert "20201014-1422eco-hello" in [o.id for o in outputs]

    file_output_storage.delete_output("STA-mini", "20201014-1422eco-hello")
    outputs = file_output_storage.list_outputs("STA-mini")
    assert len(outputs) == 4
    assert "20201014-1422eco-hello" not in [o.id for o in outputs]


def test_output_archival(file_output_storage) -> None:
    assert not file_output_storage.is_output_archived("STA-mini", "20201014-1422eco-hello")
    file_output_storage.archive_study_output("STA-mini", "20201014-1422eco-hello")
    assert file_output_storage.is_output_archived("STA-mini", "20201014-1422eco-hello")

    outputs = file_output_storage.list_outputs("STA-mini")
    assert "20201014-1422eco-hello" in [o.id for o in outputs if o.archived]

    with pytest.raises(OutputAlreadyArchived):
        file_output_storage.archive_study_output("STA-mini", "20201014-1422eco-hello")

    # TODO: check zipped on disk

    file_output_storage.unarchive_study_output("STA-mini", "20201014-1422eco-hello")
    assert not file_output_storage.is_output_archived("STA-mini", "20201014-1422eco-hello")

    outputs = file_output_storage.list_outputs("STA-mini")
    assert "20201014-1422eco-hello" in [o.id for o in outputs if not o.archived]

    with pytest.raises(OutputAlreadyUnarchived):
        file_output_storage.unarchive_study_output("STA-mini", "20201014-1422eco-hello")

    with pytest.raises(StudyNotFoundError):
        file_output_storage.archive_study_output("non-existent", "non-existent")
    with pytest.raises(OutputNotFound):
        file_output_storage.archive_study_output("STA-mini", "non-existent")

    with pytest.raises(StudyNotFoundError):
        file_output_storage.unarchive_study_output("non-existent", "non-existent")
    with pytest.raises(OutputNotFound):
        file_output_storage.unarchive_study_output("STA-mini", "non-existent")


def test_output_copy(file_output_storage: InStudyFileOutputStorage, tmp_path: Path) -> None:
    # Create a copy of the STA-mini study without outputs
    studies_dir = tmp_path / "studies"
    sta_mini_path = studies_dir / "STA-mini"
    copy_path = studies_dir / "STA-mini-copy"
    shutil.copytree(sta_mini_path, copy_path, ignore=shutil.ignore_patterns("output"))
    (copy_path / "output").mkdir()

    assert file_output_storage.list_outputs("STA-mini-copy") == []

    file_output_storage.copy_output("STA-mini", "STA-mini-copy", "20201014-1422eco-hello")
    outputs = file_output_storage.list_outputs("STA-mini-copy")
    assert [o.id for o in outputs] == ["20201014-1422eco-hello"]

    # Copy an archived output
    file_output_storage.archive_study_output("STA-mini", "20201014-1427eco")
    assert file_output_storage.is_output_archived("STA-mini", "20201014-1427eco")
    file_output_storage.copy_output("STA-mini", "STA-mini-copy", "20201014-1427eco")
    outputs = file_output_storage.list_outputs("STA-mini-copy")
    assert [o.id for o in outputs] == ["20201014-1422eco-hello", "20201014-1427eco"]
    assert file_output_storage.is_output_archived("STA-mini-copy", "20201014-1427eco")

    with pytest.raises(StudyNotFoundError):
        file_output_storage.copy_output("non-existent", "STA-mini-copy", "20201014-1427eco")
    with pytest.raises(StudyNotFoundError):
        file_output_storage.copy_output("STA-mini", "non-existent", "20201014-1427eco")
    with pytest.raises(OutputNotFound):
        file_output_storage.copy_output("STA-mini", "STA-mini-copy", "non-existent")

    with pytest.raises(OutputAlreadyExists):
        file_output_storage.copy_output("STA-mini", "STA-mini-copy", "20201014-1427eco")
    with pytest.raises(OutputAlreadyExists):
        file_output_storage.copy_output("STA-mini", "STA-mini-copy", "20201014-1422eco-hello")


def test_output_exists(file_output_storage: InStudyFileOutputStorage) -> None:
    assert file_output_storage.output_exists("STA-mini", "20201014-1427eco")
    assert not file_output_storage.output_exists("STA-mini", "non-existent")

    file_output_storage.archive_study_output("STA-mini", "20201014-1427eco")
    assert file_output_storage.is_output_archived("STA-mini", "20201014-1427eco")
    assert file_output_storage.output_exists("STA-mini", "20201014-1427eco")

    with pytest.raises(StudyNotFoundError):
        file_output_storage.output_exists("non-existent", "20201014-1427eco")


def _count_files_in_dir(dir_path: Path) -> int:
    return sum(len(d[2]) for d in os.walk(dir_path))


def _count_files_in_zip(zip_path: Path) -> int:
    with zipfile.ZipFile(zip_path, "r") as zf:
        return len(zf.namelist())


def test_export_output(file_output_storage: InStudyFileOutputStorage, tmp_path: Path) -> None:
    # We are just checking the count of files is correct as a proxy of a full content check
    expected_count = 79

    zip_path = tmp_path / "output.zip"
    file_output_storage.export_output("STA-mini", "20201014-1427eco", zip_path)
    assert zip_path.exists()
    assert _count_files_in_zip(zip_path) == expected_count

    # Check on archived study
    file_output_storage.archive_study_output("STA-mini", "20201014-1427eco")
    zip_path = tmp_path / "output2.zip"
    file_output_storage.export_output("STA-mini", "20201014-1427eco", zip_path)
    assert zip_path.exists()
    assert _count_files_in_zip(zip_path) == expected_count

    with pytest.raises(StudyNotFoundError):
        file_output_storage.export_output("non-existent", "20201014-1427eco", zip_path)
    with pytest.raises(OutputNotFound):
        file_output_storage.export_output("STA-mini", "non-existent", zip_path)


def test_write_output_to_dir(file_output_storage: InStudyFileOutputStorage, tmp_path: Path) -> None:
    # We just checking the count of files is correct as a proxy of a full content check
    expected_count = 79

    export_path = tmp_path / "export"
    export_path.mkdir()
    file_output_storage.write_output_to_dir("STA-mini", "20201014-1427eco", export_path)
    expected_path = export_path / "20201014-1427eco"
    assert expected_path.is_dir()
    assert "about-the-study" in os.listdir(expected_path)
    assert _count_files_in_dir(expected_path) == expected_count

    # Check on archived study
    file_output_storage.archive_study_output("STA-mini", "20201014-1427eco")
    export_path = tmp_path / "export2"
    export_path.mkdir()
    file_output_storage.write_output_to_dir("STA-mini", "20201014-1427eco", export_path)
    expected_path = export_path / "20201014-1427eco"
    assert expected_path.is_dir()
    assert "about-the-study" in os.listdir(expected_path)
    assert _count_files_in_dir(expected_path) == expected_count

    with pytest.raises(StudyNotFoundError):
        file_output_storage.write_output_to_dir("non-existent", "20201014-1427eco", export_path)
    with pytest.raises(OutputNotFound):
        file_output_storage.write_output_to_dir("STA-mini", "non-existent", export_path)


# TODO: add tests for aggregation, time index
