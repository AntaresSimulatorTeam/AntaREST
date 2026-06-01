# Copyright (c) 2026, RTE (https://www.rte-france.com)
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
from typing import Any
from unittest.mock import Mock

import pytest

from antarest.core.config import Config, StorageConfig, WorkspaceConfig
from antarest.core.jwt import JWTUser
from antarest.core.model import PublicMode
from antarest.core.requests import UserHasNotPermissionError
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.login.model import User
from antarest.login.utils import current_user_context
from antarest.study.model import DEFAULT_WORKSPACE_NAME, StorageMode, StudyType
from antarest.study.storage.variantstudy.repository import VariantStudyRepository
from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService
from tests.helpers import create_variant_study


def build_config(study_path: Path) -> Config:
    return Config(storage=StorageConfig(workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig(path=study_path)}))


def test_get_variant_children(tmp_path: Path, admin_user: Any) -> None:
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
        matrix_service=Mock(),
    )

    parent = create_variant_study(
        id="parent",
        name="parent",
        type=StudyType.VARIANT,
        archived=False,
        path=str(study_path),
        version="700",
        owner=User(id=2, name="me"),
        groups=[],
        public_mode=PublicMode.NONE,
        storage_mode=StorageMode.FILESYSTEM,
    )
    children = [
        create_variant_study(
            id="child1",
            name="child1",
            type=StudyType.VARIANT,
            archived=False,
            path=str(study_path),
            version="700",
            owner=User(id=2, name="me"),
            groups=[],
            public_mode=PublicMode.NONE,
            storage_mode=StorageMode.DATABASE,
        ),
        create_variant_study(
            id="child2",
            name="child2",
            type=StudyType.VARIANT,
            archived=False,
            path=str(study_path),
            version="700",
            owner=User(id=3, name="not me"),
            groups=[],
            public_mode=PublicMode.NONE,
            storage_mode=StorageMode.DATABASE,
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
