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

from pathlib import Path
from unittest.mock import Mock

import pytest

from antarest.core.config import Config, StorageConfig, WorkspaceConfig
from antarest.core.exceptions import StudyNotFoundError, VariantGenerationError
from antarest.core.interfaces.cache import CacheConstants
from antarest.core.jwt import JWTUser
from antarest.core.model import PublicMode
from antarest.core.requests import UserHasNotPermissionError
from antarest.core.tasks.model import TaskDTO, TaskResult, TaskStatus
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.login.model import User
from antarest.login.utils import current_user_context
from antarest.study.model import DEFAULT_WORKSPACE_NAME, StudyAdditionalData
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.repository import VariantStudyRepository
from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService
from tests.helpers import create_variant_study


def build_config(study_path: Path):
    return Config(storage=StorageConfig(workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig(path=study_path)}))


@pytest.mark.unit_test
def test_get(tmp_path: str, project_path) -> None:
    """
    path_to_studies
    |_study1 (d)
    |_ study2.py
        |_ settings (d)
    |_myfile (f)
    """

    # Create folders
    path_to_studies = Path(tmp_path)
    (path_to_studies / "study1").mkdir()
    (path_to_studies / "myfile").touch()
    path_study = path_to_studies / "study2.py"
    path_study.mkdir()
    (path_study / "settings").mkdir()
    (path_study / "study.antares").touch()

    data = {"titi": 43}
    sub_route = "settings"

    study = Mock()
    study.get.return_value = data
    study_factory = Mock()
    study_factory.create_from_fs.return_value = FileStudy(Mock(), study)

    study_service = VariantStudyService(
        raw_study_service=Mock(),
        cache=Mock(),
        task_service=Mock(),
        command_factory=Mock(),
        study_factory=study_factory,
        config=build_config(path_to_studies),
        repository=Mock(),
        event_bus=Mock(),
    )

    metadata = create_variant_study(id="study2.py", path=str(path_study), generation_task="1")
    study_service.exists = Mock()
    study_service.exists.return_value = False

    def task_status(*args):
        for t in [
            TaskDTO(
                id="1",
                name="generation task",
                owner=None,
                status=TaskStatus.RUNNING,
                creation_date_utc="",
                completion_date_utc=None,
                result=None,
            ),
            TaskDTO(
                id="1",
                name="generation task",
                owner=None,
                status=TaskStatus.COMPLETED,
                creation_date_utc="",
                completion_date_utc=None,
                result=TaskResult(success=False, message="error message"),
            ),
        ]:
            yield t

    study_service.task_service.status_task.side_effect = task_status()
    with pytest.raises(VariantGenerationError, match="Error while generating variant study2.py error message"):
        study_service.get(metadata=metadata, url=sub_route, depth=2)
    study_service.task_service.await_task.assert_called()

    study_service.exists.return_value = True
    output = study_service.get(metadata=metadata, url=sub_route, depth=2)

    assert output == data

    study.get.assert_called_once_with(["settings"], depth=2, formatted=True)


@pytest.mark.unit_test
def test_get_cache(tmp_path: str) -> None:
    # Create folders
    path_to_studies = Path(tmp_path)
    (path_to_studies / "study1").mkdir()
    (path_to_studies / "myfile").touch()
    path_study = path_to_studies / "study2.py"
    path_study.mkdir()
    (path_study / "settings").mkdir()
    (path_study / "study.antares").touch()

    data = {"titi": 43}
    study = Mock()
    study.get.return_value = data

    study_factory = Mock()
    study_factory.create_from_fs.return_value = FileStudy(Mock(), study)

    cache = Mock()
    cache.get.return_value = None

    study_service = VariantStudyService(
        raw_study_service=Mock(),
        cache=cache,
        task_service=Mock(),
        command_factory=Mock(),
        study_factory=study_factory,
        config=Mock(),
        repository=Mock(),
        event_bus=Mock(),
    )

    metadata = create_variant_study(id="study2.py", path=str(path_study))

    cache_id = f"{CacheConstants.RAW_STUDY}/{metadata.id}"
    study_service.exists = Mock()
    study_service.exists.return_value = True

    assert study_service.get(metadata=metadata, url="", depth=-1) == data
    cache.get.assert_called_with(cache_id)
    cache.put.assert_called_with(cache_id, data)

    cache.get.return_value = data
    assert study_service.get(metadata=metadata, url="", depth=-1) == data
    cache.get.assert_called_with(cache_id)


@pytest.mark.unit_test
def test_assert_study_exist(tmp_path: str, project_path) -> None:
    tmp = Path(tmp_path)
    (tmp / "study1").mkdir()
    (tmp / "study.antares").touch()
    path_study2 = tmp / "study2.py"
    path_study2.mkdir()
    (path_study2 / "settings").mkdir()
    (path_study2 / "study.antares").touch()
    # Input
    study_name = "study2.py"
    path_to_studies = Path(tmp_path)

    # Test & Verify
    study_service = VariantStudyService(
        raw_study_service=Mock(),
        cache=Mock(),
        task_service=Mock(),
        command_factory=Mock(),
        study_factory=Mock(),
        config=build_config(path_to_studies),
        repository=Mock(),
        event_bus=Mock(),
    )

    metadata = create_variant_study(id=study_name, path=str(path_study2))

    study_service.exists = Mock()
    study_service.exists.return_value = True
    study_service._check_study_exists(metadata)


@pytest.mark.unit_test
def test_assert_study_not_exist(tmp_path: str, project_path) -> None:
    # Create folders
    tmp = Path(tmp_path)
    (tmp / "study1").mkdir()
    (tmp / "myfile").touch()
    path_study2 = tmp / "study2.py"
    path_study2.mkdir()
    (path_study2 / "settings").mkdir()

    # Input
    study_name = "study3"
    path_to_studies = Path(tmp_path)

    # Test & Verify
    study_service = VariantStudyService(
        raw_study_service=Mock(),
        cache=Mock(),
        task_service=Mock(),
        command_factory=Mock(),
        study_factory=Mock(),
        config=build_config(path_to_studies),
        repository=Mock(),
        event_bus=Mock(),
    )

    metadata = create_variant_study(id=study_name, path=str(path_study2))

    study_service.exists = Mock()
    study_service.exists.return_value = False

    with pytest.raises(StudyNotFoundError):
        study_service._check_study_exists(metadata)


@pytest.mark.unit_test
def test_delete_study(tmp_path: Path) -> None:
    name = "my-study"
    study_path = tmp_path / name
    study_path.mkdir()
    (study_path / "study.antares").touch()

    cache = Mock()

    study_service = VariantStudyService(
        raw_study_service=Mock(),
        cache=cache,
        task_service=Mock(),
        command_factory=Mock(),
        study_factory=Mock(),
        config=build_config(tmp_path),
        repository=Mock(),
        event_bus=Mock(),
    )

    md = create_variant_study(id=name, path=str(study_path))

    study_service.delete(md)
    cache.invalidate_all.assert_called_once_with(
        [
            f"{CacheConstants.RAW_STUDY}/{name}",
            f"{CacheConstants.STUDY_FACTORY}/{name}",
        ]
    )
    assert not study_path.exists()


@pytest.mark.unit_test
def test_get_variant_children(tmp_path: Path, admin_user) -> None:
    with db():
        user_me = User(id=2, name="me")
        user_not_me = User(id=3, name="not me")
        db.session.add(user_me)
        db.session.add(user_not_me)

    jwt_user_me = JWTUser(id=user_me.id, impersonator=user_me.id, type="users")
    jwt_user_not_me = JWTUser(id=user_not_me.id, impersonator=user_not_me.id, type="users")

    name = "my-study"
    study_path = tmp_path / name
    study_path.mkdir()
    (study_path / "study.antares").touch()

    cache = Mock()
    repo_mock = Mock(spec=VariantStudyRepository)
    study_service = VariantStudyService(
        raw_study_service=Mock(),
        cache=cache,
        task_service=Mock(),
        command_factory=Mock(),
        study_factory=Mock(),
        config=build_config(tmp_path),
        repository=repo_mock,
        event_bus=Mock(),
    )

    parent = create_variant_study(
        id="parent",
        name="parent",
        type="variant",
        archived=False,
        path=str(study_path),
        version="700",
        owner=User(id=2, name="me"),
        groups=[],
        public_mode=PublicMode.NONE,
        additional_data=StudyAdditionalData(),
    )
    children = [
        create_variant_study(
            id="child1",
            name="child1",
            type="variant",
            archived=False,
            path=str(study_path),
            version="700",
            owner=User(id=2, name="me"),
            groups=[],
            public_mode=PublicMode.NONE,
            additional_data=StudyAdditionalData(),
        ),
        create_variant_study(
            id="child2",
            name="child2",
            type="variant",
            archived=False,
            path=str(study_path),
            version="700",
            owner=User(id=3, name="not me"),
            groups=[],
            public_mode=PublicMode.NONE,
            additional_data=StudyAdditionalData(),
        ),
    ]
    for jwt_user in [jwt_user_me, jwt_user_not_me, admin_user]:
        repo_mock.get.side_effect = [parent] + children
        repo_mock.get_children.side_effect = [children, [], []]

        with current_user_context(jwt_user):
            if jwt_user == jwt_user_me:
                tree = study_service.get_all_variants_children("parent")
                assert len(tree.children) == 1

            elif jwt_user == admin_user:
                tree = study_service.get_all_variants_children("parent")
                assert len(tree.children) == 2

            else:
                with pytest.raises(UserHasNotPermissionError):
                    study_service.get_all_variants_children("parent")


@pytest.mark.unit_test
def test_initialize_additional_data(tmp_path: Path) -> None:
    name = "my-study"
    study_path = tmp_path / name
    study_path.mkdir()
    (study_path / "study.antares").touch()

    md = create_variant_study(id=name, path=str(study_path))

    additional_data = StudyAdditionalData(horizon=2050, patch="{}", author="Zoro")

    study_factory = Mock()
    study_factory.create_from_fs.return_value = md

    variant_study_service = VariantStudyService(
        raw_study_service=Mock(),
        cache=Mock(),
        task_service=Mock(),
        command_factory=Mock(),
        study_factory=study_factory,
        config=build_config(tmp_path),
        repository=Mock(spec=VariantStudyRepository),
        event_bus=Mock(),
    )

    variant_study_service._read_additional_data_from_files = Mock(return_value=additional_data)

    variant_study_service.exists = Mock(return_value=False)

    assert variant_study_service.initialize_additional_data(md)
    assert md.additional_data == StudyAdditionalData()

    variant_study_service.exists = Mock(return_value=True)
    assert variant_study_service.initialize_additional_data(md)
    assert md.additional_data == additional_data

    variant_study_service._read_additional_data_from_files.side_effect = FileNotFoundError()

    assert not variant_study_service.initialize_additional_data(md)
