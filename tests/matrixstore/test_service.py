import datetime
import io
import json
import time
import typing as t
import zipfile
from unittest.mock import ANY, Mock

import numpy as np
import pandas as pd
import pytest
from fastapi import UploadFile
from starlette.datastructures import Headers

from antarest.core.jwt import JWTGroup, JWTUser
from antarest.core.requests import RequestParameters, UserHasNotPermissionError
from antarest.core.roles import RoleType
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.login.model import Group, GroupDTO, Identity, UserInfo
from antarest.matrixstore.exceptions import MatrixDataSetNotFound
from antarest.matrixstore.model import (
    Matrix,
    MatrixDataSet,
    MatrixDataSetDTO,
    MatrixDataSetRelation,
    MatrixDataSetUpdateDTO,
    MatrixInfoDTO,
)
from antarest.matrixstore.service import MatrixService

MatrixType = t.List[t.List[float]]


class TestMatrixService:
    def test_create__nominal_case(self, matrix_service: MatrixService) -> None:
        """Creates a new matrix object with the specified data."""
        # when a matrix is created (inserted) in the service
        data: MatrixType = [[1, 2, 3], [4, 5, 6]]
        matrix_id = matrix_service.create(data)

        # A "real" hash value is calculated
        assert matrix_id, "ID can't be empty"

        # The matrix is saved in the content repository as a HDF file
        bucket_dir = matrix_service.matrix_content_repository.bucket_dir
        content_path = bucket_dir.joinpath(f"{matrix_id}.hdf")
        array = pd.read_hdf(content_path).__array__()
        assert (array == np.array(data)).all()

        # A matrix object is stored in the database
        with db():
            obj = matrix_service.repo.get(matrix_id)
        assert obj is not None, f"Missing Matrix object {matrix_id}"
        assert obj.width == len(data[0])
        assert obj.height == len(data)
        now = datetime.datetime.utcnow()
        assert now - datetime.timedelta(seconds=1) <= obj.created_at <= now

    def test_create__from_numpy_array(self, matrix_service: MatrixService) -> None:
        """Creates a new matrix object with the specified data."""
        # when a matrix is created (inserted) in the service
        data = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float64)
        matrix_id = matrix_service.create(data)

        # A "real" hash value is calculated
        assert matrix_id, "ID can't be empty"

        # The matrix is saved in the content repository as an HDF file
        bucket_dir = matrix_service.matrix_content_repository.bucket_dir
        content_path = bucket_dir.joinpath(f"{matrix_id}.hdf")
        array = pd.read_hdf(content_path).__array__()
        assert (array == data).all()

        # A matrix object is stored in the database
        with db():
            obj = matrix_service.repo.get(matrix_id)
        assert obj is not None, f"Missing Matrix object {matrix_id}"
        assert obj.width == data.shape[1]
        assert obj.height == data.shape[0]
        now = datetime.datetime.utcnow()
        assert now - datetime.timedelta(seconds=1) <= obj.created_at <= now

    def test_create__side_effect(self, matrix_service: MatrixService) -> None:
        """Creates a new matrix object with the specified data, but fail during saving."""
        # if the matrix can't be created in the service
        matrix_repo = matrix_service.repo
        matrix_repo.save = Mock(side_effect=Exception("database error"))
        with pytest.raises(Exception, match="database error"):
            data: MatrixType = [[1, 2, 3], [4, 5, 6]]
            matrix_service.create(data)

        # the associated matrix file must not be deleted
        bucket_dir = matrix_service.matrix_content_repository.bucket_dir
        hdf_files = list(bucket_dir.glob("*.hdf"))
        assert hdf_files

        # Nothing is stored in the database
        with db():
            assert not db.session.query(Matrix).count()

    def test_get(self, matrix_service: MatrixService) -> None:
        """Get a matrix object from the database and the matrix content repository."""
        # when a matrix is created (inserted) in the service
        data: MatrixType = [[1, 2, 3], [4, 5, 6]]
        matrix_id = matrix_service.create(data)

        # nominal_case: we can retrieve the matrix and its content
        with db():
            obj = matrix_service.get(matrix_id)

        assert obj is not None, f"Missing Matrix object {matrix_id}"
        assert obj.width == len(data[0])
        assert obj.height == len(data)
        now = datetime.datetime.utcnow()
        local_time = time.mktime(datetime.datetime.timetuple(now))
        assert local_time - 1 <= obj.created_at <= local_time
        assert obj.data == data
        assert obj.index == list(range(len(data)))
        assert obj.columns == list(range(len(data[0])))

        # missing_case: the matrix is missing in the database
        with db():
            missing_hash = "8b1a9953c4611296a827abf8c47804d7e6c49c6b"
            obj = matrix_service.get(missing_hash)
        assert obj is None

    def test_exists(self, matrix_service: MatrixService) -> None:
        """Test the exists method."""
        # when a matrix is created (inserted) in the service
        data: MatrixType = [[1, 2, 3], [4, 5, 6]]
        matrix_id = matrix_service.create(data)

        # nominal_case: we can retrieve the matrix and its content
        with db():
            assert matrix_service.exists(matrix_id)
            missing_hash = "8b1a9953c4611296a827abf8c47804d7e6c49c6b"
            assert not matrix_service.exists(missing_hash)

    def test_delete__nominal_case(self, matrix_service: MatrixService) -> None:
        """Delete a matrix object from the matrix content repository and the database."""
        # when a matrix is created (inserted) in the service
        data: MatrixType = [[1, 2, 3], [4, 5, 6]]
        matrix_id = matrix_service.create(data)

        # When the matrix id deleted
        with db():
            matrix_service.delete(matrix_id)

        # The matrix in no more available in the content repository
        bucket_dir = matrix_service.matrix_content_repository.bucket_dir
        hdf_files = list(bucket_dir.glob("*.hdf"))
        assert not hdf_files

        # The matrix object is deleted from the database
        with db():
            assert not db.session.query(Matrix).count()

    def test_delete__missing(self, matrix_service: MatrixService) -> None:
        """Delete a matrix object from the matrix content repository and the database."""
        # When the matrix id deleted
        with db():
            missing_hash = "8b1a9953c4611296a827abf8c47804d7e6c49c6b"
            matrix_service.delete(missing_hash)

        # then, the matrix in no more available in the content repository
        bucket_dir = matrix_service.matrix_content_repository.bucket_dir
        hdf_files = list(bucket_dir.glob("*.hdf"))
        assert not hdf_files

        # The matrix object is deleted from the database
        with db():
            assert not db.session.query(Matrix).count()

    @pytest.mark.parametrize(
        "data",
        [
            pytest.param([[1, 2, 3], [4, 5, 6]], id="classic-array"),
            pytest.param([[]], id="2D-empty-array"),
        ],
    )
    @pytest.mark.parametrize("content_type", ["application/json", "text/plain"])
    def test_create_by_importation__nominal_case(
        self,
        matrix_service: MatrixService,
        data: MatrixType,
        content_type: str,
    ) -> None:
        """
        Create a new matrix by importing a file.
        The file is either a JSON file or a TSV file.
        """
        # Prepare the matrix data to import
        matrix = np.array(data, dtype=np.float64)
        if content_type == "application/json":
            # JSON format of the array using the dataframe format
            index = list(range(matrix.shape[0]))
            columns = list(range(matrix.shape[1]))
            content = json.dumps({"index": index, "columns": columns, "data": matrix.tolist()})
            buffer = io.BytesIO(content.encode("utf-8"))
            filename = "matrix.json"
            json_format = True
        else:
            # TSV format of the array (without header)
            buffer = io.BytesIO()
            np.savetxt(buffer, matrix, delimiter="\t")
            buffer.seek(0)
            filename = "matrix.txt"
            json_format = False

        # Prepare a UploadFile object using the buffer
        upload_file = _create_upload_file(filename=filename, file=buffer, content_type=content_type)

        # when a matrix is created (inserted) in the service
        info_list: t.Sequence[MatrixInfoDTO] = matrix_service.create_by_importation(upload_file, is_json=json_format)

        # Then, check the list of created matrices
        assert len(info_list) == 1
        info = info_list[0]

        # A "real" hash value is calculated
        assert info.id, "ID can't be empty"

        # The matrix is saved in the content repository as an HDF file
        bucket_dir = matrix_service.matrix_content_repository.bucket_dir
        content_path = bucket_dir.joinpath(f"{info.id}.hdf")
        if content_path.stat().st_size == 0:
            actual = np.empty(shape=1)
        else:
            actual = pd.read_hdf(content_path).__array__()
        assert (actual == matrix).all()

        # A matrix object is stored in the database
        with db():
            obj = matrix_service.repo.get(info.id)
        assert obj is not None, f"Missing Matrix object {info.id}"
        assert obj.width == matrix.shape[1]
        assert obj.height == matrix.shape[0]
        now = datetime.datetime.utcnow()
        assert now - datetime.timedelta(seconds=1) <= obj.created_at <= now

    @pytest.mark.parametrize("content_type", ["application/json", "text/plain"])
    def test_create_by_importation__zip_file(self, matrix_service: MatrixService, content_type: str) -> None:
        """
        Create a ZIP file with several matrices, using either a JSON format or a TSV format.
        All matrices of the ZIP file use the same format.
        Check that the matrices are correctly imported.
        """
        # Prepare the matrix data to import
        data_list: t.List[MatrixType] = [
            [[1, 2, 3], [4, 5, 6]],
            [[7, 8, 9, 10, 11], [17, 18, 19, 20, 21], [27, 28, 29, 30, 31]],
            [[]],
        ]
        matrix_list: t.List[np.ndarray] = [np.array(data, dtype=np.float64) for data in data_list]
        if content_type == "application/json":
            # JSON format of the array using the dataframe format
            index_list = [list(range(matrix.shape[0])) for matrix in matrix_list]
            columns_list = [list(range(matrix.shape[1])) for matrix in matrix_list]
            data_list = [matrix.tolist() for matrix in matrix_list]
            content_list = [
                json.dumps({"index": index, "columns": columns, "data": data}).encode("utf-8")
                for index, columns, data in zip(index_list, columns_list, data_list)
            ]
            json_format = True
        else:
            # TSV format of the array (without header)
            content_list = []
            for matrix in matrix_list:
                buffer = io.BytesIO()
                np.savetxt(buffer, matrix, delimiter="\t")
                content_list.append(buffer.getvalue())
            json_format = False

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for i, content in enumerate(content_list):
                suffix = {True: "json", False: "txt"}[json_format]
                zf.writestr(f"matrix-{i:1d}.{suffix}", content)
        buffer.seek(0)

        # Prepare a UploadFile object using the buffer
        upload_file = _create_upload_file(filename="matrices.zip", file=buffer, content_type="application/zip")

        # When matrices are created (inserted) in the service
        info_list: t.Sequence[MatrixInfoDTO] = matrix_service.create_by_importation(upload_file, is_json=json_format)

        # Then, check the list of created matrices
        assert len(info_list) == len(data_list)
        for info, matrix in zip(info_list, matrix_list):
            # A "real" hash value is calculated
            assert info.id, "ID can't be empty"

            # The matrix is saved in the content repository as an HDF file
            bucket_dir = matrix_service.matrix_content_repository.bucket_dir
            content_path = bucket_dir.joinpath(f"{info.id}.hdf")
            if content_path.stat().st_size == 0:
                actual = np.empty(shape=1)
            else:
                actual = pd.read_hdf(content_path).__array__()
            assert (actual == matrix).all()

            # A matrix object is stored in the database
            with db():
                obj = matrix_service.repo.get(info.id)
            assert obj is not None, f"Missing Matrix object {info.id}"
            assert obj.width == (matrix.shape[1] if matrix.size else 0)
            assert obj.height == matrix.shape[0]
            now = datetime.datetime.utcnow()
            assert now - datetime.timedelta(seconds=1) <= obj.created_at <= now


def test_dataset_lifecycle() -> None:
    content = Mock()
    repo = Mock()
    dataset_repo = Mock()
    user_service = Mock()

    service = MatrixService(repo, dataset_repo, content, Mock(), Mock(), Mock(), user_service)

    userA = RequestParameters(
        user=JWTUser(
            id=1,
            type="users",
            impersonator=1,
            groups=[JWTGroup(id="groupA", name="groupA", role=RoleType.READER)],
        )
    )
    userB = RequestParameters(
        user=JWTUser(
            id=2,
            type="users",
            impersonator=2,
            groups=[JWTGroup(id="groupB", name="groupB", role=RoleType.READER)],
        )
    )
    botA = RequestParameters(
        user=JWTUser(
            id=3,
            type="bots",
            impersonator=1,
            groups=[JWTGroup(id="groupA", name="groupA", role=RoleType.READER)],
        )
    )

    dataset_info = MatrixDataSetUpdateDTO(
        name="datasetA",
        groups=["groupA"],
        public=True,
    )
    matrices = [
        MatrixInfoDTO(
            id="m1",
            name="A",
        ),
        MatrixInfoDTO(
            id="m2",
            name="B",
        ),
    ]

    user_service.get_group.return_value = Group(id="groupA", name="groupA")
    expected = MatrixDataSet(
        name=dataset_info.name,
        public=dataset_info.public,
        owner_id=userA.user.id,
        groups=[Group(id="groupA", name="groupA")],
        created_at=ANY,
        updated_at=ANY,
        matrices=[
            MatrixDataSetRelation(name="A", matrix_id="m1"),
            MatrixDataSetRelation(name="B", matrix_id="m2"),
        ],
    )
    service.create_dataset(dataset_info, matrices, params=userA)
    assert dataset_repo.save.call_count == 1
    call = dataset_repo.save.call_args_list[0]
    assert call[0][0].name == "datasetA"
    assert call[0][0].public is True
    assert call[0][0].owner_id == userA.user.id
    groups = call[0][0].groups
    assert len(groups) == 1
    assert groups[0].id == "groupA"
    assert groups[0].name == "groupA"
    assert call[0][0].matrices == [
        MatrixDataSetRelation(name="A", matrix_id="m1"),
        MatrixDataSetRelation(name="B", matrix_id="m2"),
    ]

    somedate = datetime.datetime.now()
    dataset_repo.query.return_value = [
        MatrixDataSet(
            id="some id",
            name="datasetA",
            public=True,
            owner_id=userA.user.id,
            owner=Identity(id=userA.user.id, name="userA", type="users"),
            groups=[Group(id="groupA", name="groupA")],
            created_at=somedate,
            updated_at=somedate,
            matrices=[
                MatrixDataSetRelation(name="A", matrix=Matrix(id="m1")),
                MatrixDataSetRelation(name="B", matrix=Matrix(id="m2")),
            ],
        ),
        MatrixDataSet(
            id="some id 2",
            name="datasetB",
            public=False,
            owner_id=userB.user.id,
            owner=Identity(id=userB.user.id, name="userB", type="users"),
            groups=[Group(id="groupB", name="groupB")],
            created_at=somedate,
            updated_at=somedate,
            matrices=[
                MatrixDataSetRelation(name="A", matrix=Matrix(id="m1")),
                MatrixDataSetRelation(name="B", matrix=Matrix(id="m2")),
            ],
        ),
    ]
    res = service.list("dataset", True, botA)
    dataset_repo.query.assert_called_with("dataset", botA.user.impersonator)
    assert len(res) == 1
    assert res[0] == MatrixDataSetDTO(
        id="some id",
        name="datasetA",
        public=True,
        owner=UserInfo(id=userA.user.id, name="userA"),
        groups=[GroupDTO(id="groupA", name="groupA")],
        created_at=str(somedate),
        updated_at=str(somedate),
        matrices=[
            MatrixInfoDTO(name="A", id="m1"),
            MatrixInfoDTO(name="B", id="m2"),
        ],
    )
    service.list("dataset", False, botA)
    dataset_repo.query.assert_called_with("dataset", None)
    res = service.list("dataset", False, userB)
    assert len(res) == 2

    with pytest.raises(MatrixDataSetNotFound):
        dataset_repo.get.return_value = None
        service.update_dataset(
            "dataset_id",
            MatrixDataSetUpdateDTO(
                name="datasetA",
                groups=["groupA"],
                public=True,
            ),
            userA,
        )

    dataset_repo.get.return_value = MatrixDataSet(
        id="some id",
        name="datasetA",
        public=True,
        owner_id=userA.user.id,
        owner=Identity(id=userA.user.id, name="userA", type="users"),
        groups=[Group(id="groupA", name="groupA")],
        created_at=somedate,
        updated_at=somedate,
        matrices=[
            MatrixDataSetRelation(name="A", matrix=Matrix(id="m1")),
            MatrixDataSetRelation(name="B", matrix=Matrix(id="m2")),
        ],
    )
    with pytest.raises(UserHasNotPermissionError):
        service.update_dataset(
            "dataset_id",
            MatrixDataSetUpdateDTO(
                name="datasetA",
                groups=["groupA"],
                public=True,
            ),
            userB,
        )

    user_service.get_group.return_value = Group(id="groupB", name="groupB")
    service.update_dataset(
        "some id",
        MatrixDataSetUpdateDTO(
            name="datasetA bis",
            groups=["groupB"],
            public=False,
        ),
        botA,
    )

    user_service.get_group.assert_called_with("groupB", botA)

    service.delete_dataset("dataset", userA)
    dataset_repo.delete.assert_called_once()


def _create_upload_file(filename: str, file: io.BytesIO, content_type: str = "") -> UploadFile:
    if hasattr(UploadFile, "content_type"):
        # `content_type` attribute was replace by a read-ony property in starlette-v0.24.
        headers = Headers(headers={"content-type": content_type})
        # noinspection PyTypeChecker,PyArgumentList
        return UploadFile(filename=filename, file=file, headers=headers)
    else:
        # noinspection PyTypeChecker,PyArgumentList
        return UploadFile(filename=filename, file=file, content_type=content_type)
