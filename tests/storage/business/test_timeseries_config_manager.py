import os
import uuid
from pathlib import Path
from unittest.mock import Mock
from zipfile import ZipFile

import pytest

from antarest.study.business.config_management import ConfigManager
from antarest.study.business.timeseries_config_management import (
    TimeSeriesConfigManager,
    TSFormFields,
    TSFormFieldsForType,
    SeasonCorrelation,
)
from antarest.study.storage.rawstudy.model.filesystem.config.files import (
    ConfigPathBuilder,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import (
    FileStudyTree,
)
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy
from antarest.study.storage.variantstudy.variant_study_service import (
    VariantStudyService,
)


def get_file_study(version: int, tmpdir: Path) -> FileStudy:
    cur_dir: Path = Path(__file__).parent
    study_path = Path(tmpdir / str(uuid.uuid4()))
    os.mkdir(study_path)
    with ZipFile(
        cur_dir / "assets" / f"empty_study_{version}.zip"
    ) as zip_output:
        zip_output.extractall(path=study_path)
    config = ConfigPathBuilder.build(study_path, "1")
    return FileStudy(config, FileStudyTree(Mock(), config))


@pytest.fixture
def file_study_820(tmpdir: Path) -> FileStudy:
    return get_file_study(820, tmpdir)


@pytest.fixture
def file_study_720(tmpdir: Path) -> FileStudy:
    return get_file_study(720, tmpdir)


def test_ts_field_values(file_study_820: FileStudy, file_study_720: FileStudy):
    command_factory_mock = Mock()
    command_factory_mock.command_context = CommandContext.construct()

    raw_study_service = Mock(spec=RawStudyService)

    variant_study_service = Mock(
        spec=VariantStudyService, command_factory=command_factory_mock
    )
    variant_study_service.get_raw.return_value = file_study_820

    config_manager = TimeSeriesConfigManager(
        StudyStorageService(raw_study_service, variant_study_service),
    )

    study = VariantStudy()

    assert config_manager.get_ts_field_values(study) == TSFormFields(
        load=TSFormFieldsForType(
            stochasticTsStatus=False,
            number=1,
            refresh=False,
            refreshInterval=100,
            seasonCorrelation=SeasonCorrelation.ANNUAL,
            storeInInput=False,
            storeInOutput=False,
            intraModal=False,
            interModal=False,
        ),
        hydro=TSFormFieldsForType(
            stochasticTsStatus=False,
            number=1,
            refresh=False,
            refreshInterval=100,
            seasonCorrelation=SeasonCorrelation.ANNUAL,
            storeInInput=False,
            storeInOutput=False,
            intraModal=False,
            interModal=False,
        ),
        thermal=TSFormFieldsForType(
            stochasticTsStatus=False,
            number=1,
            refresh=False,
            refreshInterval=100,
            seasonCorrelation=None,
            storeInInput=False,
            storeInOutput=False,
            intraModal=False,
            interModal=False,
        ),
        wind=None,
        solar=None,
        renewables=TSFormFieldsForType(
            stochasticTsStatus=False,
            number=None,
            refresh=None,
            refreshInterval=None,
            seasonCorrelation=None,
            storeInInput=None,
            storeInOutput=None,
            intraModal=False,
            interModal=False,
        ),
        ntc=TSFormFieldsForType(
            stochasticTsStatus=False,
            number=None,
            refresh=None,
            refreshInterval=None,
            seasonCorrelation=None,
            storeInInput=None,
            storeInOutput=None,
            intraModal=False,
            interModal=None,
        ),
    )

    variant_study_service.get_raw.return_value = file_study_720

    assert config_manager.get_ts_field_values(study) == TSFormFields(
        load=TSFormFieldsForType(
            stochasticTsStatus=False,
            number=1,
            refresh=False,
            refreshInterval=100,
            seasonCorrelation=SeasonCorrelation.ANNUAL,
            storeInInput=False,
            storeInOutput=False,
            intraModal=False,
            interModal=False,
        ),
        hydro=TSFormFieldsForType(
            stochasticTsStatus=False,
            number=1,
            refresh=False,
            refreshInterval=100,
            seasonCorrelation=SeasonCorrelation.ANNUAL,
            storeInInput=False,
            storeInOutput=False,
            intraModal=False,
            interModal=False,
        ),
        thermal=TSFormFieldsForType(
            stochasticTsStatus=False,
            number=1,
            refresh=False,
            refreshInterval=100,
            seasonCorrelation=None,
            storeInInput=False,
            storeInOutput=False,
            intraModal=False,
            interModal=False,
        ),
        wind=TSFormFieldsForType(
            stochasticTsStatus=False,
            number=1,
            refresh=False,
            refreshInterval=100,
            seasonCorrelation=SeasonCorrelation.ANNUAL,
            storeInInput=False,
            storeInOutput=False,
            intraModal=False,
            interModal=False,
        ),
        solar=TSFormFieldsForType(
            stochasticTsStatus=False,
            number=1,
            refresh=False,
            refreshInterval=100,
            seasonCorrelation=SeasonCorrelation.ANNUAL,
            storeInInput=False,
            storeInOutput=False,
            intraModal=False,
            interModal=False,
        ),
        renewables=None,
        ntc=None,
    )
