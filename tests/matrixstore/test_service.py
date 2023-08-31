import datetime
import io
import time
from unittest.mock import ANY, Mock
from zipfile import ZIP_DEFLATED, ZipFile

import numpy as np
import pytest
from fastapi import UploadFile

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


class TestMatrixService:
    def test_create__nominal_case(self, matrix_service: MatrixService):
        """Creates a new matrix object with the specified data."""
        # when a matrix is created (inserted) in the service
        data = [[1, 2, 3], [4, 5, 6]]
        matrix_id = matrix_service.create(data)

        # A "real" hash value is calculated
        assert matrix_id, "ID can't be empty"

        # The matrix is saved in the content repository as a TSV file
        bucket_dir = matrix_service.matrix_content_repository.bucket_dir
        content_path = bucket_dir.joinpath(f"{matrix_id}.tsv")
        array = np.loadtxt(content_path)
        assert array.all() == np.array(data).all()

        # A matrix object is stored in the database
        with db():
            obj = matrix_service.repo.get(matrix_id)
        assert obj is not None, f"Missing Matrix object {matrix_id}"
        assert obj.width == len(data[0])
        assert obj.height == len(data)
        now = datetime.datetime.utcnow()
        assert now - datetime.timedelta(seconds=1) <= obj.created_at <= now

    def test_create__from_numpy_array(self, matrix_service: MatrixService):
        """Creates a new matrix object with the specified data."""
        # when a matrix is created (inserted) in the service
        data = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float64)
        matrix_id = matrix_service.create(data)

        # A "real" hash value is calculated
        assert matrix_id, "ID can't be empty"

        # The matrix is saved in the content repository as a TSV file
        bucket_dir = matrix_service.matrix_content_repository.bucket_dir
        content_path = bucket_dir.joinpath(f"{matrix_id}.tsv")
        array = np.loadtxt(content_path)
        assert array.all() == data.all()

        # A matrix object is stored in the database
        with db():
            obj = matrix_service.repo.get(matrix_id)
        assert obj is not None, f"Missing Matrix object {matrix_id}"
        assert obj.width == data.shape[1]
        assert obj.height == data.shape[0]
        now = datetime.datetime.utcnow()
        assert now - datetime.timedelta(seconds=1) <= obj.created_at <= now

    def test_create__side_effect(self, matrix_service: MatrixService):
        """Creates a new matrix object with the specified data, but fail during saving."""
        # if the matrix can't be created in the service
        matrix_repo = matrix_service.repo
        matrix_repo.save = Mock(side_effect=Exception("database error"))
        with pytest.raises(Exception, match="database error"):
            data = [[1, 2, 3], [4, 5, 6]]
            matrix_service.create(data)

        # the associated matrix file must not be deleted
        bucket_dir = matrix_service.matrix_content_repository.bucket_dir
        tsv_files = list(bucket_dir.glob("*.tsv"))
        assert tsv_files

        # Nothing is stored in the database
        with db():
            assert not db.session.query(Matrix).count()

    def test_get(self, matrix_service):
        """Get a matrix object from the database and the matrix content repository."""
        # when a matrix is created (inserted) in the service
        data = [[1, 2, 3], [4, 5, 6]]
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

    def test_exists(self, matrix_service):
        """Test the exists method."""
        # when a matrix is created (inserted) in the service
        data = [[1, 2, 3], [4, 5, 6]]
        matrix_id = matrix_service.create(data)

        # nominal_case: we can retrieve the matrix and its content
        with db():
            assert matrix_service.exists(matrix_id)
            missing_hash = "8b1a9953c4611296a827abf8c47804d7e6c49c6b"
            assert not matrix_service.exists(missing_hash)

    def test_delete__nominal_case(self, matrix_service: MatrixService):
        """Delete a matrix object from the matrix content repository and the database."""
        # when a matrix is created (inserted) in the service
        data = [[1, 2, 3], [4, 5, 6]]
        matrix_id = matrix_service.create(data)

        # When the matrix id deleted
        with db():
            matrix_service.delete(matrix_id)

        # The matrix in no more available in the content repository
        bucket_dir = matrix_service.matrix_content_repository.bucket_dir
        tsv_files = list(bucket_dir.glob("*.tsv"))
        assert not tsv_files

        # The matrix object is deleted from the database
        with db():
            assert not db.session.query(Matrix).count()

    def test_delete__missing(self, matrix_service: MatrixService):
        """Delete a matrix object from the matrix content repository and the database."""
        # When the matrix id deleted
        with db():
            missing_hash = "8b1a9953c4611296a827abf8c47804d7e6c49c6b"
            matrix_service.delete(missing_hash)

        # then, the matrix in no more available in the content repository
        bucket_dir = matrix_service.matrix_content_repository.bucket_dir
        tsv_files = list(bucket_dir.glob("*.tsv"))
        assert not tsv_files

        # The matrix object is deleted from the database
        with db():
            assert not db.session.query(Matrix).count()


def test_dataset_lifecycle():
    content = Mock()
    repo = Mock()
    dataset_repo = Mock()
    user_service = Mock()

    service = MatrixService(
        repo, dataset_repo, content, Mock(), Mock(), Mock(), user_service
    )

    userA = RequestParameters(
        user=JWTUser(
            id=1,
            type="users",
            impersonator=1,
            groups=[
                JWTGroup(id="groupA", name="groupA", role=RoleType.READER)
            ],
        )
    )
    userB = RequestParameters(
        user=JWTUser(
            id=2,
            type="users",
            impersonator=2,
            groups=[
                JWTGroup(id="groupB", name="groupB", role=RoleType.READER)
            ],
        )
    )
    botA = RequestParameters(
        user=JWTUser(
            id=3,
            type="bots",
            impersonator=1,
            groups=[
                JWTGroup(id="groupA", name="groupA", role=RoleType.READER)
            ],
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
    dataset_repo.save.assert_called_with(expected)

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
    dataset_repo.save.assert_called_with(
        MatrixDataSet(
            id="some id",
            name="datasetA bis",
            public=False,
            groups=[Group(id="groupB", name="groupB")],
            updated_at=ANY,
        )
    )

    service.delete_dataset("dataset", userA)
    dataset_repo.delete.assert_called_once()


def test_import():
    # Init Mock
    repo_content = Mock()
    repo = Mock()

    file_str = "1\t2\t3\t4\t5\n6\t7\t8\t9\t10"
    matrix_content = str.encode(file_str)

    # Expected
    id = "123"
    exp_matrix_info = [MatrixInfoDTO(id="123", name="matrix.txt")]
    exp_matrix = Matrix(id=id, width=5, height=2)
    # Test
    service = MatrixService(
        repo=repo,
        repo_dataset=Mock(),
        matrix_content_repository=repo_content,
        file_transfer_manager=Mock(),
        task_service=Mock(),
        config=Mock(),
        user_service=Mock(),
    )
    service.repo.get.return_value = None
    service.matrix_content_repository.save.return_value = id
    service.repo.save.return_value = exp_matrix

    # CSV importation
    zip_file = UploadFile(
        filename="matrix.txt",
        file=io.BytesIO(matrix_content),
        content_type="test/plain",
    )
    matrix = service.create_by_importation(zip_file)
    assert matrix[0].name == exp_matrix_info[0].name
    assert matrix[0].id is not None

    # Zip importation
    zip_content = io.BytesIO()
    with ZipFile(zip_content, "w", ZIP_DEFLATED) as output_data:
        output_data.writestr("matrix.txt", file_str)

    zip_content.seek(0)
    zip_file = UploadFile(
        filename="Matrix.zip", file=zip_content, content_type="application/zip"
    )
    matrix = service.create_by_importation(zip_file)
    assert matrix == exp_matrix_info
