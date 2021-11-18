from pathlib import Path
from unittest.mock import Mock

import pytest

from antarest.core.interfaces.cache import CacheConstants
from antarest.matrixstore.service import MatrixService
from antarest.study.model import RawStudy, DEFAULT_WORKSPACE_NAME
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import (
    IniFileNode,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import (
    InputSeriesMatrix,
)
from antarest.study.storage.rawstudy.model.filesystem.raw_file_node import (
    RawFileNode,
)
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.variantstudy.business.matrix_constants_generator import (
    GeneratorMatrixConstants,
)
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy
from antarest.study.storage.variantstudy.variant_study_service import (
    VariantStudyService,
)
from tests.storage.business.test_raw_study_service import build_config


@pytest.mark.unit_test
def test_edit_study(tmp_path: Path) -> None:
    # Mock
    (tmp_path / "my-uuid").mkdir()
    (tmp_path / "my-uuid/study.antares").touch()

    study = Mock()
    study.get_node.return_value = Mock(spec=IniFileNode)

    study_factory = Mock()
    study_factory.create_from_fs.return_value = None, study

    cache = Mock()

    repository = Mock()
    repository.get = Mock(return_value=Mock(spec=VariantStudy))

    variant_study_service = VariantStudyService(
        task_service=Mock(),
        cache=cache,
        raw_study_service=Mock(),
        command_factory=CommandFactory(
            generator_matrix_constants=Mock(spec=GeneratorMatrixConstants),
            matrix_service=Mock(spec=MatrixService),
        ),
        study_factory=study_factory,
        patch_service=Mock(),
        repository=repository,
        event_bus=Mock(),
        config=build_config(tmp_path),
    )
    variant_study_service.append_command = Mock()
    variant_study_service.command_factory.command_context.matrix_service.create = Mock(
        return_value="id"
    )

    # Input
    url = "url/to/change"
    new = {"Hello": "World"}

    id = "my-uuid"
    md = VariantStudy(
        id=id,
        path=str(tmp_path / "my-uuid"),
    )
    res = variant_study_service.edit_study(md, url, new)

    assert (
        variant_study_service.append_command.call_args_list[-1][0][1].action
        == "update_config"
    )

    cache.invalidate_all.assert_called_once_with(
        [
            f"{CacheConstants.RAW_STUDY}/{id}",
            f"{CacheConstants.STUDY_FACTORY}/{id}",
        ]
    )
    assert new == res

    study.get_node.return_value = Mock(spec=InputSeriesMatrix)
    variant_study_service.edit_study(md, url, [[1, 2, 3]])
    assert (
        variant_study_service.append_command.call_args_list[-1][0][1].action
        == "replace_matrix"
    )

    study.get_node.return_value = Mock(spec=RawFileNode)
    variant_study_service.edit_study(md, "settings/comments", "new comment")
    assert (
        variant_study_service.append_command.call_args_list[-1][0][1].action
        == "update_comments"
    )
    with pytest.raises(NotImplementedError):
        study.get_node.return_value = Mock()
        variant_study_service.edit_study(md, Mock(), Mock())
