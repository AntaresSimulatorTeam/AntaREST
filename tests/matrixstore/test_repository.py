from datetime import datetime
from pathlib import Path
from typing import Optional
from unittest.mock import Mock

from sqlalchemy import create_engine, and_

from antarest.common.config import Config, MatrixStoreConfig, SecurityConfig
from antarest.common.persistence import Base
from antarest.common.utils.fastapi_sqlalchemy import DBSessionMiddleware, db
from antarest.login.model import User, Password, Group
from antarest.login.repository import UserRepository, GroupRepository
from antarest.matrixstore.model import (
    Matrix,
    MatrixFreq,
    MatrixContent,
    MatrixMetadata,
    MatrixUserMetadata,
)
from antarest.matrixstore.repository import (
    MatrixRepository,
    MatrixContentRepository,
    MatrixMetadataRepository,
)


def test_db_cyclelife():
    engine = create_engine("sqlite:///:memory:", echo=True)
    Base.metadata.create_all(engine)
    DBSessionMiddleware(
        Mock(),
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )

    with db():
        repo = MatrixRepository()
        m = Matrix(
            id="hello",
            freq=MatrixFreq.WEEKLY,
            created_at=datetime.now(),
        )
        repo.save(m)
        assert m.id
        assert m == repo.get(m.id)
        assert [m] == repo.get_by_freq(freq=MatrixFreq.WEEKLY)
        assert [] == repo.get_by_freq(freq=MatrixFreq.HOURLY)

        assert repo.exists(m.id)

        repo.delete(m.id)
        assert repo.get(m.id) is None


def test_bucket_cyclelife(tmp_path: Path):
    config = Config(matrixstore=MatrixStoreConfig(bucket=tmp_path))
    repo = MatrixContentRepository(config)

    a = MatrixContent(
        index=["1", "2"], columns=["a", "b"], data=[[1, 2], [3, 4]]
    )
    b = MatrixContent(
        index=["3", "4"], columns=["c", "d"], data=[[5, 6], [7, 8]]
    )

    aid = repo.save(a)
    assert aid == repo.save(a)

    bid = repo.save(b)
    assert aid != bid

    assert a == repo.get(aid)
    assert b == repo.get(bid)

    repo.delete(aid)
    assert repo.get(aid) is None


def test_metadata():
    engine = create_engine("sqlite:///:memory:", echo=True)
    Base.metadata.create_all(engine)
    DBSessionMiddleware(
        Mock(),
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )

    with db():
        repo = MatrixRepository()
        m = Matrix(
            id="hello",
            freq=MatrixFreq.WEEKLY,
            created_at=datetime.now(),
        )
        repo.save(m)

        user_repo = UserRepository(Config(security=SecurityConfig()))
        user_repo.save(User(name="foo", password=Password("bar")))

        group_repo = GroupRepository()
        group = group_repo.save(Group(name="group"))

        meta_repo = MatrixMetadataRepository()

        metadata = MatrixMetadata(
            matrix_id="hello", owner_id=1, key="name", value="some ts"
        )
        metadata2 = MatrixMetadata(
            matrix_id="hello", owner_id=1, key="public", value="true"
        )
        user_metadata = MatrixUserMetadata(
            matrix_id="hello",
            owner_id=1,
            metadata_={"name": metadata, "public": metadata2},
            groups=[group],
        )
        meta_repo.save(user_metadata)
        meta_res: Optional[MatrixUserMetadata] = meta_repo.get("hello", 1)
        assert meta_res is not None
        assert meta_res.metadata_["name"].value == "some ts"
        assert meta_res.metadata_["public"].value == "true"
        assert len(meta_res.groups) == 1
        assert len(db.session.query(MatrixMetadata).all()) == 2

        user_metadata_update = MatrixUserMetadata(
            matrix_id="hello",
            owner_id=1,
            metadata_={
                "name": metadata,
                "additional": MatrixMetadata(
                    matrix_id="hello",
                    owner_id=1,
                    key="additional",
                    value="test",
                ),
            },
        )
        meta_repo.save(user_metadata_update)
        meta_res: Optional[MatrixUserMetadata] = meta_repo.get("hello", 1)
        assert meta_res is not None
        assert meta_res.metadata_["name"].value == "some ts"
        assert meta_res.metadata_["additional"].value == "test"
        assert "public" not in meta_res.metadata_
        assert len(meta_res.groups) == 1
        assert len(db.session.query(MatrixMetadata).all()) == 2

        user_metadata_update_group = MatrixUserMetadata(
            matrix_id="hello", owner_id=1, groups=[]
        )
        meta_repo.save(user_metadata_update_group)
        meta_res: Optional[MatrixUserMetadata] = meta_repo.get("hello", 1)
        assert meta_res is not None
        assert meta_res.metadata_["name"].value == "some ts"
        assert meta_res.metadata_["additional"].value == "test"
        assert "public" not in meta_res.metadata_
        assert len(meta_res.groups) == 0
        assert len(db.session.query(MatrixMetadata).all()) == 2

        user_metadata_delete_all = MatrixUserMetadata(
            matrix_id="hello", owner_id=1, metadata_={}, groups=[]
        )
        meta_repo.save(user_metadata_delete_all)
        meta_res: Optional[MatrixUserMetadata] = meta_repo.get("hello", 1)
        assert meta_res is not None
        assert len(meta_res.metadata_.keys()) == 0
        assert len(meta_res.groups) == 0
        assert len(db.session.query(MatrixMetadata).all()) == 0


def test_metadata_query():
    engine = create_engine("sqlite:///:memory:", echo=True)
    Base.metadata.create_all(engine)
    DBSessionMiddleware(
        Mock(),
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )

    with db():
        repo = MatrixRepository()
        m = Matrix(
            id="hello",
            freq=MatrixFreq.WEEKLY,
            created_at=datetime.now(),
        )
        repo.save(m)
        repo.save(
            Matrix(
                id="hallo",
                freq=MatrixFreq.HOURLY,
                created_at=datetime.now(),
            )
        )

        user_repo = UserRepository(Config(security=SecurityConfig()))
        user_repo.save(User(name="foo", password=Password("bar")))

        group_repo = GroupRepository()
        group = group_repo.save(Group(name="group"))
        group2 = group_repo.save(Group(name="group2"))

        meta_repo = MatrixMetadataRepository()

        user_1_metadata_1 = MatrixUserMetadata(
            matrix_id="hello",
            owner_id=0,
            metadata_={
                "name": MatrixMetadata(
                    matrix_id="hello",
                    owner_id=0,
                    key="name",
                    value="another ts",
                ),
                "tag2": MatrixMetadata(
                    matrix_id="hello", owner_id=0, key="tag2", value="false"
                ),
            },
            groups=[group2],
        )
        user_2_metadata_1 = MatrixUserMetadata(
            matrix_id="hello",
            owner_id=1,
            metadata_={
                "name": MatrixMetadata(
                    matrix_id="hello", owner_id=1, key="name", value="some ts"
                ),
                "tag": MatrixMetadata(
                    matrix_id="hello", owner_id=1, key="tag", value="true"
                ),
            },
            groups=[group],
        )
        user_2_metadata_2 = MatrixUserMetadata(
            matrix_id="hallo",
            owner_id=1,
            metadata_={
                "name": MatrixMetadata(
                    matrix_id="hallo", owner_id=1, key="name", value="da ts"
                ),
                "tag": MatrixMetadata(
                    matrix_id="hallo", owner_id=1, key="tag", value="false"
                ),
            },
            groups=[group],
        )
        meta_repo.save(user_1_metadata_1)
        meta_repo.save(user_2_metadata_1)
        meta_repo.save(user_2_metadata_2)

        res = meta_repo.query("ts")
        assert len(res) == 3
        res = meta_repo.query("some")
        assert len(res) == 1
        res = meta_repo.query(None, {"tag": "true"})
        assert len(res) == 1
        res = meta_repo.query("ts", {"tag": "true", "tag2": "true"})
        assert len(res) == 0
        res = meta_repo.query("another")
        assert len(res) == 1
        res = meta_repo.query("another", {"tag2": "false"})
        assert len(res) == 1
        res = meta_repo.query("another", {"tag": "true"})
        assert len(res) == 0
        res = meta_repo.query(None, {}, 0)
        assert len(res) == 1
