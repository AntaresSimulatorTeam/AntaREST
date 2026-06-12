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

from pathlib import Path, PosixPath
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from antarest.core.config import Config, StorageConfig, WorkspaceConfig
from antarest.core.exceptions import WorkspaceNotFound
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.favorite.model import FavoriteExternalDirectory, FavoriteExternalDirectoryDTO
from antarest.favorite.repository import FavoriteExternalDirectoryRepository
from antarest.favorite.service import FavoriteExternalDirectoryService
from antarest.login.utils import current_user_context
from antarest.study.directory_exceptions import DirectoryNotFoundError


def test_add_favorite_external_directory_failure_when_path_does_not_exist(tmp_path: Path):
    # Trying to add an external directory whose path doesn't exist to the favorites
    workspace = "validspace"
    config = Config(storage=StorageConfig(tmp_dir=tmp_path))
    config.storage.workspaces.update({workspace: WorkspaceConfig(path=tmp_path)})
    path_to_favorite = PosixPath(tmp_path) / workspace
    path_to_favorite.mkdir(parents=True, exist_ok=True)
    mock_path = path_to_favorite / "notapath" / "to" / "favorite" / "directory"
    mock_favorite_external_directory_repository = Mock(spec=FavoriteExternalDirectoryRepository)

    mock_favorite_external_directory_repository.save.return_value = FavoriteExternalDirectory(
        path=str(path_to_favorite), workspace=workspace
    )
    favorite_service = FavoriteExternalDirectoryService(
        mock_favorite_external_directory_repository, workspace_config=config
    )

    with current_user_context(DEFAULT_ADMIN_USER):
        with pytest.raises(DirectoryNotFoundError, match=f"404: Directory '{mock_path}' not found"):
            favorite_service.add_favorite(str(mock_path), workspace)


def test_add_favorite_external_directory_failure_when_workspace_does_not_exist(tmp_path: Path):
    # Trying to add an external directory to a non-existing workspace
    config = Config(storage=StorageConfig(tmp_dir=tmp_path))
    path_to_favorite = PosixPath(tmp_path / "path" / "to" / "favorite" / "directory")
    non_existing_workspace = ""
    mock_favorite_external_directory_repository = Mock(spec=FavoriteExternalDirectoryRepository)
    mock_favorite_external_directory_repository.save.return_value = FavoriteExternalDirectory(
        workspace=non_existing_workspace, path=str(path_to_favorite)
    )
    favorite_service = FavoriteExternalDirectoryService(
        mock_favorite_external_directory_repository, workspace_config=config
    )

    with pytest.raises(WorkspaceNotFound, match=f"422: Workspace {''} not found"):
        favorite_service.add_favorite(str(path_to_favorite), non_existing_workspace)


def test_list_favorite_external_directory_success_returns_empty_list_when_no_favorite_exists(tmp_path: Path):
    # getting the external directories in the favorites, but returns an empty list due to no favorite existing
    config = Config(storage=StorageConfig(tmp_dir=tmp_path))
    expected_favorite_list = []
    mocked_favorite_external_directory_repository = Mock(spec=FavoriteExternalDirectoryRepository)
    mocked_favorite_external_directory_repository.get_all.return_value = []
    favorite_service = FavoriteExternalDirectoryService(
        mocked_favorite_external_directory_repository, workspace_config=config
    )

    actual_favorite_list = favorite_service.list_favorites()
    assert actual_favorite_list == expected_favorite_list


def test_list_favorite_external_directory_success_returns_two_favorites(tmp_path: Path):
    # getting the external directories in the favorites, and returns two favorites
    config = Config(storage=StorageConfig(tmp_dir=tmp_path))
    expected_favorite_1 = FavoriteExternalDirectoryDTO(
        path=PosixPath("path\\to\\favorite\\directory_1"), workspace="validspace"
    )
    expected_favorite_2 = FavoriteExternalDirectoryDTO(
        path=PosixPath("path\\to\\favorite\\directory_2"), workspace="validspace"
    )
    expected_favorite_list = [expected_favorite_1, expected_favorite_2]

    favorite_1 = FavoriteExternalDirectory(path="path\\to\\favorite\\directory_1", workspace="validspace")
    favorite_2 = FavoriteExternalDirectory(path="path\\to\\favorite\\directory_2", workspace="validspace")
    mocked_favorite_external_directory_repository = Mock(spec=FavoriteExternalDirectoryRepository)
    mocked_favorite_external_directory_repository.get_all.return_value = [favorite_1, favorite_2]
    favorite_service = FavoriteExternalDirectoryService(
        mocked_favorite_external_directory_repository, workspace_config=config
    )

    actual_favorite_list = favorite_service.list_favorites()
    assert actual_favorite_list == expected_favorite_list


def test_add_favorite_external_directory_success_added_one_favorite(tmp_path: Path):
    # adding an external directory to the favorites, and then checking that the favorite is added
    config = Config(storage=StorageConfig(tmp_dir=tmp_path))
    config.storage.workspaces.update({"validspace": WorkspaceConfig(path=tmp_path)})
    expected_favorite_dto = FavoriteExternalDirectoryDTO(
        path=PosixPath("path\\to\\favorite\\directory"), workspace="validspace"
    )
    expected_fav_directory = FavoriteExternalDirectory(path="path\\to\\favorite\\directory", workspace="validspace")
    directory_to_favorite = tmp_path / "validspace" / "path" / "to" / "favorite" / "directory"
    directory_to_favorite.mkdir(parents=True, exist_ok=True)

    mocked_favorite_external_directory_repository = Mock(spec=FavoriteExternalDirectoryRepository)
    mocked_favorite_external_directory_repository.save.return_value = expected_fav_directory
    favorite_service = FavoriteExternalDirectoryService(
        mocked_favorite_external_directory_repository, workspace_config=config
    )

    with current_user_context(DEFAULT_ADMIN_USER):
        actual_favorite_dto = favorite_service.add_favorite(str(directory_to_favorite), "validspace")

    mocked_favorite_external_directory_repository.get_all.return_value = [expected_fav_directory]
    actual_favorite_dto_list = favorite_service.list_favorites()

    assert actual_favorite_dto == expected_favorite_dto
    assert actual_favorite_dto_list == [expected_favorite_dto]


def test_delete_favorite_external_directory_failure_when_directory_does_not_exist(tmp_path: Path):
    # deleting an external directory from the favorites, but no errors are raised because the directory does not exist
    config = Config(storage=StorageConfig(tmp_dir=tmp_path))
    inexisting_directory_path = ""
    mocked_favorite_external_directory_repository = Mock(spec=FavoriteExternalDirectoryRepository)
    favorite_service = FavoriteExternalDirectoryService(
        mocked_favorite_external_directory_repository, workspace_config=config
    )
    mocked_favorite_external_directory_repository.delete.return_value = False

    with pytest.raises(
        HTTPException,
        match=f"404: Favorite external directory with path {inexisting_directory_path} and workspace invalidspace not found",
    ):
        favorite_service.delete_favorite(path=inexisting_directory_path, workspace="invalidspace")


def test_delete_favorite_external_directory_success_deleted_one_favorite(tmp_path: Path):
    # deleting an external directory from the favorites, and then checking that the favorite is deleted
    config = Config(storage=StorageConfig(tmp_dir=tmp_path))
    mock_favorite_external_directory_repository = Mock(spec=FavoriteExternalDirectoryRepository)
    favorite_service = FavoriteExternalDirectoryService(
        mock_favorite_external_directory_repository, workspace_config=config
    )
    mocked_favorite_external_directory = FavoriteExternalDirectory(
        path="path\\to\\favorite\\directory", workspace="validspace"
    )

    mock_favorite_external_directory_repository.get_all.return_value = [mocked_favorite_external_directory]
    actual_favorite_list = favorite_service.list_favorites()
    assert len(actual_favorite_list) == 1

    favorite_service.delete_favorite(workspace="validspace", path="path\\to\\favorite\\directory")
    mock_favorite_external_directory_repository.delete.assert_called_once()

    mock_favorite_external_directory_repository.get_all.return_value = []
    actual_favorite_list = favorite_service.list_favorites()
    assert len(actual_favorite_list) == 0
    assert actual_favorite_list == []
