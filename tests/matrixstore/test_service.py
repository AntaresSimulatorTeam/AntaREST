import datetime
import io
from unittest.mock import Mock, ANY
from zipfile import ZipFile, ZIP_DEFLATED

import pytest
from fastapi import UploadFile
from sqlalchemy import create_engine

from antarest.core.jwt import JWTUser, JWTGroup
from antarest.core.requests import (
    RequestParameters,
    UserHasNotPermissionError,
)
from antarest.core.roles import RoleType
from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware
from antarest.dbmodel import Base
from antarest.login.model import Group, GroupDTO, Identity, UserInfo
from antarest.matrixstore.exceptions import MatrixDataSetNotFound
from antarest.matrixstore.model import (
    MatrixDTO,
    Matrix,
    MatrixContent,
    MatrixDataSetUpdateDTO,
    MatrixDataSet,
    MatrixDataSetRelation,
    MatrixDataSetDTO,
    MatrixInfoDTO,
)
from antarest.matrixstore.service import MatrixService


def test_save():
    engine = create_engine("sqlite:///:memory:", echo=True)
    Base.metadata.create_all(engine)
    DBSessionMiddleware(
        Mock(),
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )

    # Init Mock
    repo_content = Mock()
    repo_content.save.return_value = "my-id"

    repo = Mock()

    # Input
    dto = [[1, 2]]

    # Expected
    matrix = Matrix(
        id="my-id",
        width=2,
        height=1,
        created_at=ANY,
    )

    repo.get.return_value = None

    # Test
    service = MatrixService(
        repo=repo,
        repo_dataset=Mock(),
        matrix_content_repository=repo_content,
        user_service=Mock(),
    )
    id = service.create(dto)

    # Verify
    assert id == "my-id"
    repo.save.assert_called_once_with(matrix)
    repo_content.save.assert_called_once_with(dto)


def test_get():
    # Init Mock
    content = Mock()
    content.get.return_value = MatrixContent(
        data=[[1, 2]],
        index=["1"],
        columns=["a", "b"],
    )

    repo = Mock()
    repo.get.return_value = Matrix(
        id="my-id",
        width=2,
        height=1,
        created_at=datetime.datetime.fromtimestamp(42),
    )

    repo_meta = Mock()

    # Expected
    exp = MatrixDTO(
        id="my-id",
        created_at=42,
        updated_at=101,
        width=2,
        height=1,
        data=[[1, 2]],
        index=["1"],
        columns=["a", "b"],
    )

    # Test
    service = MatrixService(repo, repo_meta, content, Mock())
    res = service.get("my-id")
    assert exp == res


def test_delete():
    content = Mock()
    repo = Mock()
    repo_meta = Mock()

    service = MatrixService(repo, repo_meta, content, Mock())
    service.delete("my-id")
    content.delete.assert_called_once_with("my-id")
    repo.delete.assert_called_once_with("my-id")


def test_dataset_lifecycle():
    content = Mock()
    repo = Mock()
    dataset_repo = Mock()
    user_service = Mock()

    service = MatrixService(repo, dataset_repo, content, user_service)

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
