from pathlib import Path, PosixPath
from unittest.mock import Mock

import pytest
from fastapi import HTTPException


class FavoriteExternalDirectory:
    def __init__(self, path: PosixPath, workspace: str):
        self.path = path
        self.workspace = workspace


class FavoriteExternalDirectoryRepository:
    # def __init__(self):
    #    self._session = session

    def save(self, favorite_external_directory: FavoriteExternalDirectory) -> FavoriteExternalDirectory:
        return favorite_external_directory


class FavoriteExternalDirectoryService:
    def __init__(self, favorite_external_directory_repository: FavoriteExternalDirectoryRepository):
        self._favorite_external_directory_repository = favorite_external_directory_repository

    def add_favorite(self, mock_path: PosixPath, workspace: str) -> FavoriteExternalDirectory:

        # try:
        #     favorite_external_directory = FavoriteExternalDirectory(path=mock_path, workspace=workspace)
        #     self._favorite_external_directory_repository.save(favorite_external_directory)
        #     return favorite_external_directory
        # except PathNotExistsError as e:
        #     raise e
        if Path.exists(workspace / mock_path):
            favorite_external_directory = FavoriteExternalDirectory(path=mock_path, workspace=workspace)
            self._favorite_external_directory_repository.save(favorite_external_directory)
            return favorite_external_directory
        else:
            raise HTTPException(status_code=404, detail=f"Path {mock_path} does not exist.")

    def list_favorites(self) -> list[FavoriteExternalDirectory]:
        return []


def test_add_favorite_external_directory_failure_when_path_does_not_exist():
    # Trying to add an external directory whose path doesn't exist to the favorites
    mock_path = PosixPath("path/to/non/existing/directory")
    workspace = "validspace"
    mock_favorite_external_directory_repository = Mock(spec=FavoriteExternalDirectoryRepository)

    mock_favorite_external_directory_repository.save.return_value = FavoriteExternalDirectory(
        path=mock_path, workspace=workspace
    )
    favorite_service = FavoriteExternalDirectoryService(mock_favorite_external_directory_repository)

    with pytest.raises(HTTPException, match=f"Path {mock_path} does not exist."):
        favorite_service.add_favorite(mock_path, workspace)


def test_list_favorite_external_directory_success_returns_empty_list_when_no_favorite_exists():
    # getting the external directories in the favorites, but returns an empty list due to no favorite existing
    expected_favorite_list = []
    mocked_favorite_external_directory_repository = Mock(spec=FavoriteExternalDirectoryRepository)
    mocked_favorite_external_directory_repository.get.return_value = []
    favorite_service = FavoriteExternalDirectoryService(mocked_favorite_external_directory_repository)

    actual_favorite_list = favorite_service.list_favorites()
    assert actual_favorite_list == expected_favorite_list

    pass


def test_list_favorite_external_directory_success_returns_two_favorites():
    pass


def test_add_favorite_external_directory_success_added_one_favorite():
    # adding an external directory to the favorites
    pass


def test_delete_favorite_external_directory_success_no_errors_when_directory_does_not_exist():
    pass


def test_delete_favorite_external_directory_success_deleted_one_favorite():
    pass
