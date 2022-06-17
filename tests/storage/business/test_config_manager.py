from pathlib import Path
from unittest.mock import Mock

from antarest.study.business.config_management import (
    ConfigManager,
    OutputVariable,
)
from antarest.study.model import RawStudy
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import (
    FileStudyTree,
)
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.update_config import (
    UpdateConfig,
)
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy
from antarest.study.storage.variantstudy.variant_study_service import (
    VariantStudyService,
)


def test_thematic_trimming_config():
    command_context = CommandContext.construct()
    command_factory_mock = Mock()
    command_factory_mock.command_context = command_context
    raw_study_service = Mock(spec=RawStudyService)
    variant_study_service = Mock(
        spec=VariantStudyService, command_factory=command_factory_mock
    )
    config_manager = ConfigManager(
        storage_service=StudyStorageService(
            raw_study_service, variant_study_service
        ),
    )

    study = VariantStudy()
    config = FileStudyTreeConfig(
        study_path=Path("somepath"),
        path=Path("somepath"),
        study_id="",
        version=-1,
        areas={},
        sets={},
    )
    file_tree_mock = Mock(spec=FileStudyTree, context=Mock(), config=config)
    variant_study_service.get_raw.return_value = FileStudy(
        config=config, tree=file_tree_mock
    )
    file_tree_mock.get.side_effect = [
        {},
        {"variable selection": {"select_var -": ["AVL DTG"]}},
        {
            "variable selection": {
                "selected_vars_reset": False,
                "select_var +": ["CONG. FEE (ALG.)"],
            }
        },
    ]

    expected = {var: True for var in OutputVariable}
    assert config_manager.get_thematic_trimming(study) == expected
    expected[OutputVariable.AVL_DTG] = False
    assert config_manager.get_thematic_trimming(study) == expected
    expected = {var: False for var in OutputVariable}
    expected[OutputVariable.CONG_FEE_ALG] = True
    assert config_manager.get_thematic_trimming(study) == expected

    new_config = {var: True for var in OutputVariable}
    new_config[OutputVariable.COAL] = False
    config_manager.set_thematic_trimming(study, new_config)
    assert variant_study_service.append_commands.called_with(
        UpdateConfig(
            target="settings/generaldata/variable selection",
            data={"select_var -": [str(OutputVariable.COAL)]},
            command_context=command_context,
        )
    )
    new_config = {var: False for var in OutputVariable}
    new_config[OutputVariable.DTG_BY_PLANT] = True
    config_manager.set_thematic_trimming(study, new_config)
    assert variant_study_service.append_commands.called_with(
        UpdateConfig(
            target="settings/generaldata/variable selection",
            data={
                "selected_vars_reset": False,
                "select_var +": [str(OutputVariable.DTG_BY_PLANT)],
            },
            command_context=command_context,
        )
    )
