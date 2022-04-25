import os
import uuid
from pathlib import Path
from unittest.mock import Mock, patch
from zipfile import ZipFile

import pytest
from checksumdir import dirhash

from antarest.study.storage.rawstudy.model.filesystem.config.files import (
    ConfigPathBuilder,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    transform_name_to_id,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    ChildNotFoundError,
)
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import (
    FileStudyTree,
)
from antarest.study.storage.variantstudy.model.command.create_area import (
    CreateArea,
)
from antarest.study.storage.variantstudy.model.command.create_link import (
    CreateLink,
)
from antarest.study.storage.variantstudy.model.command.remove_area import (
    RemoveArea,
)
from antarest.study.storage.variantstudy.model.command.remove_link import (
    RemoveLink,
)
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)


class TestRemoveLink:
    def test_validation(self, empty_study: FileStudy):
        pass

    @staticmethod
    def make_study(tmpdir: Path, version: int) -> FileStudy:
        study_dir: Path = (
            Path(__file__).parent.parent.parent.parent
            / "storage"
            / "business"
            / "assets"
            / f"empty_study_{version}.zip"
        )
        study_path = Path(tmpdir / str(uuid.uuid4()))
        os.mkdir(study_path)
        with ZipFile(study_dir) as zip_output:
            zip_output.extractall(path=study_path)
        config = ConfigPathBuilder.build(study_path, "1")
        return FileStudy(config, FileStudyTree(Mock(), config))

    @pytest.mark.parametrize("version", [(810), (820)])
    @pytest.mark.unit_test
    def test_apply(
        self, tmpdir: Path, command_context: CommandContext, version: int
    ):
        empty_study = self.make_study(tmpdir, version)
        area1 = "Area1"
        area1_id = transform_name_to_id(area1)
        area2 = "Area2"
        area2_id = transform_name_to_id(area2)

        CreateArea.parse_obj(
            {
                "area_name": area1,
                "command_context": command_context,
            }
        ).apply(empty_study)

        CreateArea.parse_obj(
            {
                "area_name": area2,
                "command_context": command_context,
            }
        ).apply(empty_study)

        hash_before_link = dirhash(empty_study.config.study_path, "md5")

        CreateLink(
            area1=area1_id,
            area2=area2_id,
            parameters={},
            command_context=command_context,
            series=[[0]],
        ).apply(empty_study)

        output = RemoveLink(
            area1=area1_id,
            area2=area2_id,
            command_context=command_context,
        ).apply(empty_study)

        assert output.status
        assert (
            dirhash(empty_study.config.study_path, "md5") == hash_before_link
        )

    @pytest.mark.unit_test
    def test_match(self, command_context: CommandContext):
        base = RemoveLink(
            area1="foo", area2="bar", command_context=command_context
        )
        other_match = RemoveLink(
            area1="foo", area2="bar", command_context=command_context
        )
        other_not_match = RemoveLink(
            area1="foo", area2="baz", command_context=command_context
        )
        other_other = RemoveArea(id="id", command_context=command_context)
        assert base.match(other_match)
        assert not base.match(other_not_match)
        assert not base.match(other_other)
        assert base.match_signature() == "remove_link%foo%bar"
        assert base.get_inner_matrices() == []

    @pytest.mark.unit_test
    @patch(
        "antarest.study.storage.variantstudy.model.command.utils_extractor.CommandExtraction.extract_link",
    )
    def test_revert(self, mock_extract_link, command_context: CommandContext):
        base = RemoveLink(
            area1="foo", area2="bar", command_context=command_context
        )
        study = FileStudy(config=Mock(), tree=Mock())
        mock_extract_link.side_effect = ChildNotFoundError("")
        base.revert([], study)
        mock_extract_link.assert_called_with(study, "bar", "foo")
        assert base.revert(
            [
                CreateLink(
                    area1="foo",
                    area2="bar",
                    series=[[0]],
                    command_context=command_context,
                )
            ],
            None,
        ) == [
            CreateLink(
                area1="foo",
                area2="bar",
                series=[[0]],
                command_context=command_context,
            )
        ]

    @pytest.mark.unit_test
    def test_create_diff(self, command_context: CommandContext):
        base = RemoveLink(
            area1="foo", area2="bar", command_context=command_context
        )
        other_match = RemoveLink(
            area1="foo", area2="bar", command_context=command_context
        )
        assert base.create_diff(other_match) == []
