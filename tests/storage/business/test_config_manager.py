from pathlib import Path
from unittest.mock import Mock

from antarest.study.business.thematic_trimming_management import (
    FIELDS_INFO,
    ThematicTrimmingManager,
    ThematicTrimmingFormFields,
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
    thematic_trimming_manager = ThematicTrimmingManager(
        storage_service=StudyStorageService(
            raw_study_service, variant_study_service
        ),
    )

    study = VariantStudy(version="820")
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
        {"variables selection": {"select_var -": ["AVL DTG"]}},
        {"variables selection": {"select_var -": ["AVL DTG"]}},
        {
            "variables selection": {
                "selected_vars_reset": False,
                "select_var +": ["CONG. FEE (ALG.)"],
            }
        },
    ]

    def get_expected(value=True) -> ThematicTrimmingFormFields:
        return ThematicTrimmingFormFields.construct(
            **{
                field_name: value
                for field_name in [
                    name
                    for name, info in FIELDS_INFO.items()
                    if info.get("start_version", -1) <= config.version  # type: ignore
                ]
            }
        )

    assert thematic_trimming_manager.get_field_values(study) == get_expected()

    config.version = 800
    expected = get_expected().copy(update={"avl_dtg": False})
    assert thematic_trimming_manager.get_field_values(study) == expected

    config.version = 820
    expected = get_expected().copy(update={"avl_dtg": False})
    assert thematic_trimming_manager.get_field_values(study) == expected

    config.version = 840
    expected = get_expected(False).copy(update={"cong_fee_alg": True})
    assert thematic_trimming_manager.get_field_values(study) == expected

    new_config = get_expected().copy(update={"coal": False})
    thematic_trimming_manager.set_field_values(study, new_config)
    assert variant_study_service.append_commands.called_with(
        UpdateConfig(
            target="settings/generaldata/variables selection",
            data={"select_var -": [FIELDS_INFO["coal"]["path"]]},
            command_context=command_context,
        )
    )

    new_config = get_expected(False).copy(update={"renw_1": True})
    thematic_trimming_manager.set_field_values(study, new_config)
    assert variant_study_service.append_commands.called_with(
        UpdateConfig(
            target="settings/generaldata/variables selection",
            data={
                "selected_vars_reset": False,
                "select_var +": [FIELDS_INFO["renw_1"]["path"]],
            },
            command_context=command_context,
        )
    )

    assert len(FIELDS_INFO) == 63
