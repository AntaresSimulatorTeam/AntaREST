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
from pathlib import Path, PurePosixPath
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


@pytest.fixture
def favorite_external_directory_service(
    tmp_path: Path,
) -> tuple[FavoriteExternalDirectoryService, Mock, Config, str, Path]:
    """
    Fixture that creates a FavoriteExternalDirectoryService with a mocked repository
    and a temporary workspace configuration.

    Returns:
        A tuple of (FavoriteExternalDirectoryService, Mock repository, Config, workspace_name, workspace_path)
    """
    # Create a config with the temporary path
    config = Config(storage=StorageConfig(tmp_dir=tmp_path))

    # Define workspace name and its actual path on disk
    workspace_name = "validspace"
    workspace_path = tmp_path / "ext_workspace"
    workspace_path.mkdir(parents=True, exist_ok=True)

    # Configure the workspace: workspace_name -> workspace_path
    config.storage.workspaces.update({workspace_name: WorkspaceConfig(path=workspace_path)})

    # Create a mock repository
    mock_repository = Mock(spec=FavoriteExternalDirectoryRepository)

    # Create the service
    service = FavoriteExternalDirectoryService(
        favorite_external_directory_repository=mock_repository, workspace_config=config
    )

    return service, mock_repository, config, workspace_name, workspace_path


def test_add_favorite_external_directory_failure_when_path_does_not_exist(tmp_path: Path):
    # Trying to add an external directory whose path doesn't exist to the favorites
    mock_not_a_path = Path("notapath") / "to" / "favorite" / "directory"
    workspace = "validspace"
    config = Config(storage=StorageConfig(tmp_dir=tmp_path))
    config.storage.workspaces.update({workspace: WorkspaceConfig(path=tmp_path)})
    path_to_favorite = Path(tmp_path) / workspace
    path_to_favorite.mkdir(parents=True, exist_ok=True)
    mock_favorite_external_directory_repository = Mock(spec=FavoriteExternalDirectoryRepository)

    mock_favorite_external_directory_repository.save.return_value = FavoriteExternalDirectory(
        path=mock_not_a_path.as_posix(), workspace=workspace
    )
    favorite_service = FavoriteExternalDirectoryService(
        mock_favorite_external_directory_repository, workspace_config=config
    )

    with current_user_context(DEFAULT_ADMIN_USER):
        with pytest.raises(DirectoryNotFoundError, match=f"404: Directory '{mock_not_a_path.as_posix()}' not found"):
            favorite_service.add_favorite(mock_not_a_path.as_posix(), workspace)


def test_add_favorite_external_directory_failure_when_workspace_does_not_exist(tmp_path: Path):
    # Trying to add an external directory to a non-existing workspace
    config = Config(storage=StorageConfig(tmp_dir=tmp_path))
    path_to_favorite = PurePosixPath(tmp_path / "path" / "to" / "favorite" / "directory")
    non_existing_workspace = ""
    mock_favorite_external_directory_repository = Mock(spec=FavoriteExternalDirectoryRepository)
    mock_favorite_external_directory_repository.save.return_value = FavoriteExternalDirectory(
        workspace=non_existing_workspace, path=path_to_favorite.as_posix()
    )
    favorite_service = FavoriteExternalDirectoryService(
        mock_favorite_external_directory_repository, workspace_config=config
    )

    with pytest.raises(WorkspaceNotFound, match=f"422: Workspace {''} not found"):
        favorite_service.add_favorite(path_to_favorite.as_posix(), non_existing_workspace)


def test_list_favorite_external_directory_success_returns_empty_list_when_no_favorite_exists(
    favorite_external_directory_service: tuple[FavoriteExternalDirectoryService, Mock, Config, str, Path],
):
    # getting the external directories in the favorites, but returns an empty list due to no favorite existing
    service, mock_repo, config, workspace_name, workspace_path = favorite_external_directory_service
    expected_favorite_list = []
    mock_repo.get_all.return_value = []

    actual_favorite_list = service.list_favorites()
    assert actual_favorite_list == expected_favorite_list


def test_list_favorite_external_directory_success_returns_two_favorites(
    favorite_external_directory_service: tuple[FavoriteExternalDirectoryService, Mock, Config, str, Path],
):
    # getting the external directories in the favorites, and returns two favorites
    service, mock_repo, config, workspace_name, workspace_path = favorite_external_directory_service
    expected_favorite_1 = FavoriteExternalDirectoryDTO(
        path=PurePosixPath("path/to/favorite/directory_1"), workspace=workspace_name
    )
    expected_favorite_2 = FavoriteExternalDirectoryDTO(
        path=PurePosixPath("path/to/favorite/directory_2"), workspace=workspace_name
    )
    expected_favorite_list = [expected_favorite_1, expected_favorite_2]

    favorite_1 = FavoriteExternalDirectory(path="path/to/favorite/directory_1", workspace=workspace_name)
    favorite_2 = FavoriteExternalDirectory(path="path/to/favorite/directory_2", workspace=workspace_name)
    mock_repo.get_all.return_value = [favorite_1, favorite_2]

    actual_favorite_list = service.list_favorites()
    assert actual_favorite_list == expected_favorite_list


def test_add_favorite_external_directory_success_added_one_favorite(
    favorite_external_directory_service: tuple[FavoriteExternalDirectoryService, Mock, Config, str, Path],
):
    # adding an external directory to the favorites, and then checking that the favorite is added
    service, mock_repo, config, workspace_name, workspace_path = favorite_external_directory_service
    expected_favorite_dto = FavoriteExternalDirectoryDTO(
        path=PurePosixPath("path/to/favorite/directory"), workspace=workspace_name
    )
    expected_fav_directory = FavoriteExternalDirectory(path="path/to/favorite/directory", workspace=workspace_name)

    # Create the directory relative to the workspace path
    directory_to_favorite = workspace_path / "path" / "to" / "favorite" / "directory"
    directory_to_favorite.mkdir(parents=True, exist_ok=True)

    mock_repo.save.return_value = expected_fav_directory

    with current_user_context(DEFAULT_ADMIN_USER):
        # Pass the path relative to workspace, not the full path
        actual_favorite_dto = service.add_favorite("path/to/favorite/directory", workspace_name)

    mock_repo.get_all.return_value = [expected_fav_directory]
    actual_favorite_dto_list = service.list_favorites()

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


def test_delete_favorite_external_directory_success_deleted_one_favorite(
    favorite_external_directory_service: tuple[FavoriteExternalDirectoryService, Mock, Config, str, Path],
):
    # deleting an external directory from the favorites, and then checking that the favorite is deleted
    service, mock_repo, config, workspace_name, workspace_path = favorite_external_directory_service
    directory = "path/to/favorite/directory"

    mocked_favorite_external_directory = FavoriteExternalDirectory(path=directory, workspace=workspace_name)

    # Setup: List shows one favorite initially
    mock_repo.get_all.return_value = [mocked_favorite_external_directory]
    actual_favorite_list = service.list_favorites()
    assert len(actual_favorite_list) == 1

    # Delete the favorite
    mock_repo.delete.return_value = True
    service.delete_favorite(workspace=workspace_name, path=directory)
    mock_repo.delete.assert_called_once_with(workspace=workspace_name, path=directory)

    # Verify: List shows no favorites after deletion
    mock_repo.get_all.return_value = []
    actual_favorite_list = service.list_favorites()
    assert len(actual_favorite_list) == 0
    assert actual_favorite_list == []
