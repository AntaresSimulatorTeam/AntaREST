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
import uuid
from pathlib import Path, PurePosixPath
from unittest.mock import Mock

import pytest

from antarest.core.config import Config, StorageConfig, WorkspaceConfig
from antarest.favorite.model import (
    FavoriteDirectory,
    FavoriteDirectoryDTO,
    FavoriteExternalDirectory,
    FavoriteExternalDirectoryDTO,
    FavoriteStudy,
    FavoriteStudyDTO,
)
from antarest.favorite.repository import (
    FavoriteDirectoryRepository,
    FavoriteExternalDirectoryRepository,
    FavoriteStudyRepository,
)
from antarest.favorite.service import (
    FavoriteAggregateService,
    FavoriteDirectoryService,
    FavoriteExternalDirectoryService,
    FavoriteStudyService,
)
from antarest.study.model import Directory, Study


@pytest.fixture
def mock_favorite_external_directory_service(
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


@pytest.fixture
def mock_favorite_directory_service() -> tuple[FavoriteDirectoryService, Mock]:
    """
    Fixture that creates a FavoriteDirectoryService with a mocked repository.

    Returns:
        A tuple of (FavoriteDirectoryService, Mock repository)
    """
    # Create a mock repository
    mock_repository = Mock(spec=FavoriteDirectoryRepository)

    # Create the service
    service = FavoriteDirectoryService(favorite_directory_repository=mock_repository)

    return service, mock_repository


@pytest.fixture
def mock_favorite_study_service() -> tuple[FavoriteStudyService, Mock]:
    """
    Fixture that creates a FavoriteStudyService with a mocked repository.

    Returns:
        A tuple of (FavoriteStudyService, Mock repository)
    """
    # Create a mock repository
    mock_repository = Mock(spec=FavoriteStudyRepository)

    # Create the service
    service = FavoriteStudyService(favorite_study_repository=mock_repository)

    return service, mock_repository


def test_favorite_aggregate_success_no_favorite_added(
    mock_favorite_external_directory_service: tuple[FavoriteExternalDirectoryService, Mock, Config, str, Path],
    mock_favorite_directory_service: tuple[FavoriteDirectoryService, Mock],
    mock_favorite_study_service: tuple[FavoriteStudyService, Mock],
):
    # checking we have no favorite with the aggregate method due to no favorite being added
    favorite_study_service, mock_fav_study_repo = mock_favorite_study_service
    favorite_directory_service, mock_fav_dir_repo = mock_favorite_directory_service
    favorite_external_directory_service, mock_fav_ext_dir_repo, config, workspace_name, workspace_path = (
        mock_favorite_external_directory_service
    )

    mock_fav_dir_repo.get_all.return_value = []
    mock_fav_study_repo.get_all.return_value = []
    mock_fav_ext_dir_repo.get_all.return_value = []

    aggregate_service = FavoriteAggregateService(
        favorite_study_service, favorite_directory_service, favorite_external_directory_service
    )

    aggregate_list = aggregate_service.list_favorites()
    assert aggregate_list.studies == []
    assert aggregate_list.directories == []
    assert aggregate_list.external_directories == []


def test_favorite_aggregate_success_added_each_type_of_favorite(
    mock_favorite_external_directory_service: tuple[FavoriteExternalDirectoryService, Mock, Config, str, Path],
    mock_favorite_directory_service: tuple[FavoriteDirectoryService, Mock],
    mock_favorite_study_service: tuple[FavoriteStudyService, Mock],
):
    # checking we have no favorite with the aggregate method due to no favorite being added
    favorite_study_service, mock_fav_study_repo = mock_favorite_study_service
    favorite_directory_service, mock_fav_dir_repo = mock_favorite_directory_service
    favorite_external_directory_service, mock_fav_ext_dir_repo, config, workspace_name, workspace_path = (
        mock_favorite_external_directory_service
    )

    # creating test variables for favorites

    directory_id = str(uuid.uuid4())
    study_id = str(uuid.uuid4())

    # external directory favorite
    expected_favorite_ext_directory_dto = FavoriteExternalDirectoryDTO(
        path=PurePosixPath("path/to/favorite/directory"), workspace=workspace_name
    )
    expected_fav_ext_directory = FavoriteExternalDirectory(path="path/to/favorite/directory", workspace=workspace_name)

    # directory favorite
    mock_directory = Mock(spec=Directory)
    mock_directory.id = directory_id
    mock_directory.name = "directory_name"
    expected_favorite_directory_dto = FavoriteDirectoryDTO(directory_id=directory_id, directory_name="directory_name")
    expected_favorite_directory = FavoriteDirectory(user_id=1, directory_id=directory_id)
    expected_favorite_directory.directory = mock_directory

    # study favorite
    mock_study = Mock(spec=Study)
    mock_study.id = study_id
    mock_study.name = "study_name"
    expected_favorite_study_dto = FavoriteStudyDTO(study_id=study_id, study_name="study_name")
    expected_favorite_study = FavoriteStudy(user_id=1, study_id=study_id)
    expected_favorite_study.study = mock_study

    mock_fav_study_repo.get_all.return_value = [expected_favorite_study]
    mock_fav_dir_repo.get_all.return_value = [expected_favorite_directory]
    mock_fav_ext_dir_repo.get_all.return_value = [expected_fav_ext_directory]

    aggregate_service = FavoriteAggregateService(
        favorite_study_service, favorite_directory_service, favorite_external_directory_service
    )

    aggregate_list = aggregate_service.list_favorites()
    assert aggregate_list.studies == [expected_favorite_study_dto]
    assert aggregate_list.directories == [expected_favorite_directory_dto]
    assert aggregate_list.external_directories == [expected_favorite_ext_directory_dto]
