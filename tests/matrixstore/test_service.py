import datetime
from unittest.mock import Mock, ANY

import pytest

from antarest.common.jwt import JWTUser, JWTGroup
from antarest.common.requests import (
    RequestParameters,
    UserHasNotPermissionError,
)
from antarest.common.roles import RoleType
from antarest.login.model import Group, GroupDTO
from antarest.matrixstore.exceptions import MetadataKeyNotAllowed
from antarest.matrixstore.model import (
    MatrixDTO,
    MatrixFreq,
    Matrix,
    MatrixContent,
    MatrixUserMetadata,
    MatrixMetadata,
    MatrixUserMetadataQuery,
    MatrixMetadataDTO,
)
from antarest.matrixstore.service import MatrixService


def test_save():
    # Init Mock
    repo_content = Mock()
    repo_content.save.return_value = "my-id"

    repo = Mock()

    # Input
    dto = MatrixDTO(
        freq=MatrixFreq.WEEKLY,
        created_at=42,
        data=[[1, 2]],
        index=["1", "2"],
        columns=["a", "b"],
    )

    # Expected
    matrix = Matrix(
        id="my-id",
        freq=MatrixFreq.WEEKLY,
        created_at=ANY,
    )

    content = MatrixContent(
        index=["1", "2"], columns=["a", "b"], data=[[1, 2]]
    )

    # Test
    service = MatrixService(
        repo=repo, repo_meta=Mock(), content=repo_content, user_service=Mock()
    )
    id = service.create(dto)

    # Verify
    assert id == "my-id"
    repo.save.assert_called_once_with(matrix)
    repo_content.save.assert_called_once_with(content)


def test_get():
    # Init Mock
    content = Mock()
    content.get.return_value = MatrixContent(
        data=[[1, 2]],
        index=["1", "2"],
        columns=["a", "b"],
    )

    repo = Mock()
    repo.get.return_value = Matrix(
        id="my-id",
        freq=MatrixFreq.WEEKLY,
        created_at=datetime.datetime.fromtimestamp(42),
    )

    repo_meta = Mock()

    # Expected
    exp = MatrixDTO(
        id="my-id",
        freq=MatrixFreq.WEEKLY,
        created_at=42,
        updated_at=101,
        data=[[1, 2]],
        index=["1", "2"],
        columns=["a", "b"],
    )

    # Test
    service = MatrixService(repo, repo_meta, content, Mock())
    res = service.get("my-id")
    assert exp == res


def test_get_by_type_freq():
    content = Mock()
    content.get.return_value = MatrixContent(
        data=[[1, 2]],
        index=["1", "2"],
        columns=["a", "b"],
    )

    repo = Mock()
    repo.get_by_freq.return_value = [
        Matrix(
            id="my-id",
            freq=MatrixFreq.WEEKLY,
            created_at=datetime.datetime.fromtimestamp(42),
        )
    ]

    repo_meta = Mock()

    # Expected
    exp = MatrixDTO(
        id="my-id",
        freq=MatrixFreq.WEEKLY,
        created_at=42,
        updated_at=101,
        data=[[1, 2]],
        index=["1", "2"],
        columns=["a", "b"],
    )

    # Test
    service = MatrixService(repo, repo_meta, content, Mock())
    res = service.get_by_freq(freq=MatrixFreq.WEEKLY)
    assert [exp] == res
    repo.get_by_freq.assert_called_once_with(MatrixFreq.WEEKLY)


def test_delete():
    content = Mock()
    repo = Mock()
    repo_meta = Mock()

    service = MatrixService(repo, repo_meta, content, Mock())
    service.delete("my-id")
    content.delete.assert_called_once_with("my-id")
    repo.delete.assert_called_once_with("my-id")


def test_metadata_update():
    content = Mock()
    repo = Mock()
    repo_meta = Mock()
    user_service = Mock()

    service = MatrixService(repo, repo_meta, content, user_service)

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

    with pytest.raises(UserHasNotPermissionError):
        service.update_metadata("id", 1, {"hello": "world"}, userB)

    with pytest.raises(MetadataKeyNotAllowed):
        service.update_metadata("id", 1, {"name": "world"}, botA)

    expected = MatrixUserMetadata(
        matrix_id="id",
        owner_id=1,
        metadata_={
            "id": MatrixMetadata(
                matrix_id="id",
                owner_id=1,
                key="tag",
                value="val",
            )
        },
    )
    service.update_metadata("id", 1, {"tag": "val"}, userA)
    repo_meta.save.assert_called_with(expected)

    user_service.get_group.return_value = Group(id="groupA", name="groupA")
    service.update_group("id", 1, ["groupA"], userA)
    expected = MatrixUserMetadata(
        matrix_id="id", owner_id=1, groups=[Group(id="groupA", name="groupA")]
    )
    user_service.get_group.assert_called_with("groupA", userA)
    repo_meta.save.assert_called_with(expected)

    repo_meta.get.return_value = None
    service.set_name("id", 1, "hello", userA)
    expected = MatrixUserMetadata(
        matrix_id="id",
        owner_id=1,
        metadata_={
            "name": MatrixMetadata(
                matrix_id="id",
                owner_id=1,
                key="name",
                value="hello",
            )
        },
    )
    repo_meta.save.assert_called_with(expected)

    repo_meta.get.return_value = MatrixUserMetadata(
        matrix_id="id",
        owner_id=1,
        metadata_={
            "name": MatrixMetadata(
                matrix_id="id",
                owner_id=1,
                key="name",
                value="hello",
            )
        },
    )
    service.set_public("id", 1, True, userA)
    expected = MatrixUserMetadata(
        matrix_id="id",
        owner_id=1,
        metadata_={
            "name": MatrixMetadata(
                matrix_id="id",
                owner_id=1,
                key="name",
                value="hello",
            ),
            "is_public": MatrixMetadata(
                matrix_id="id",
                owner_id=1,
                key="is_public",
                value="True",
            ),
        },
    )
    assert expected.is_public()
    repo_meta.save.assert_called_with(expected)

    repo_meta.query.return_value = [
        MatrixUserMetadata(
            matrix_id="id",
            owner_id=1,
            metadata_={
                "name": MatrixMetadata(
                    matrix_id="id",
                    owner_id=1,
                    key="name",
                    value="hello",
                ),
                "is_public": MatrixMetadata(
                    matrix_id="id",
                    owner_id=1,
                    key="is_public",
                    value="True",
                ),
            },
        ),
        MatrixUserMetadata(
            matrix_id="id2",
            owner_id=2,
            metadata_={
                "name": MatrixMetadata(
                    matrix_id="id2",
                    owner_id=2,
                    key="name",
                    value="hello",
                )
            },
        ),
        MatrixUserMetadata(
            matrix_id="id3",
            owner_id=3,
            metadata_={
                "tag": MatrixMetadata(
                    matrix_id="id3",
                    owner_id=3,
                    key="tag",
                    value="hello",
                )
            },
            groups=[Group(id="groupA", name="groupA")],
        ),
    ]
    resA = service.list(MatrixUserMetadataQuery(), params=userA)
    assert resA == [
        MatrixMetadataDTO(
            id="id", name="hello", metadata={}, groups=[], public=True
        ),
        MatrixMetadataDTO(
            id="id3",
            name=None,
            metadata={"tag": "hello"},
            groups=[GroupDTO(id="groupA", name="groupA")],
            public=False,
        ),
    ]
    resB = service.list(MatrixUserMetadataQuery(), params=userB)
    assert resB == [
        MatrixMetadataDTO(
            id="id", name="hello", metadata={}, groups=[], public=True
        ),
        MatrixMetadataDTO(
            id="id2", name="hello", metadata={}, groups=[], public=False
        ),
    ]
    resAbot = service.list(MatrixUserMetadataQuery(), params=botA)
    assert resAbot == [
        MatrixMetadataDTO(
            id="id", name="hello", metadata={}, groups=[], public=True
        ),
        MatrixMetadataDTO(
            id="id3",
            name=None,
            metadata={"tag": "hello"},
            groups=[GroupDTO(id="groupA", name="groupA")],
            public=False,
        ),
    ]
