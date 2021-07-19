from datetime import datetime
from pathlib import Path
from typing import Optional
from unittest.mock import Mock

from sqlalchemy import create_engine, and_

from antarest.core.config import Config, MatrixStoreConfig, SecurityConfig
from antarest.core.persistence import Base
from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware, db
from antarest.login.model import User, Password, Group, Identity
from antarest.login.repository import UserRepository, GroupRepository
from antarest.matrixstore.model import (
    Matrix,
    MatrixContent,
    MatrixDataSet,
    MatrixDataSetRelation,
)
from antarest.matrixstore.repository import (
    MatrixRepository,
    MatrixContentRepository,
    MatrixDataSetRepository,
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
            created_at=datetime.now(),
        )
        repo.save(m)
        assert m.id
        assert m == repo.get(m.id)
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


def test_dataset():
    engine = create_engine("sqlite:///:memory:", echo=True)
    Base.metadata.create_all(engine)
    DBSessionMiddleware(
        Mock(),
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )

    with db():
        repo = MatrixRepository()

        user_repo = UserRepository(Config(security=SecurityConfig()))
        user = user_repo.save(User(name="foo", password=Password("bar")))

        group_repo = GroupRepository()
        group = group_repo.save(Group(name="group"))

        dataset_repo = MatrixDataSetRepository()

        m1 = Matrix(
            id="hello",
            created_at=datetime.now(),
        )
        repo.save(m1)
        m2 = Matrix(
            id="world",
            created_at=datetime.now(),
        )
        repo.save(m2)

        dataset = MatrixDataSet(
            name="some name",
            public=True,
            owner_id=user.id,
            groups=[group],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        matrix_relation = MatrixDataSetRelation(name="m1")
        matrix_relation.matrix_id = "hello"
        dataset.matrices.append(matrix_relation)
        matrix_relation = MatrixDataSetRelation(name="m2")
        matrix_relation.matrix_id = "world"
        dataset.matrices.append(matrix_relation)

        dataset = dataset_repo.save(dataset)
        dataset_query_result: Optional[MatrixDataSet] = dataset_repo.get(
            dataset.id
        )
        assert dataset_query_result is not None
        assert dataset_query_result.name == "some name"
        assert len(dataset_query_result.matrices) == 2

        dataset_update = MatrixDataSet(
            id=dataset.id,
            name="some name change",
            public=False,
            updated_at=datetime.now(),
        )
        dataset_repo.save(dataset_update)
        dataset_query_result: Optional[MatrixDataSet] = dataset_repo.get(
            dataset.id
        )
        assert dataset_query_result is not None
        assert dataset_query_result.name == "some name change"
        assert dataset_query_result.owner_id == user.id


def test_datastore_query():
    engine = create_engine("sqlite:///:memory:", echo=True)
    Base.metadata.create_all(engine)
    DBSessionMiddleware(
        Mock(),
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )

    with db():
        user_repo = UserRepository(Config(security=SecurityConfig()))
        user1 = user_repo.save(User(name="foo", password=Password("bar")))
        user2 = user_repo.save(User(name="hello", password=Password("world")))

        repo = MatrixRepository()
        m1 = Matrix(
            id="hello",
            created_at=datetime.now(),
        )
        repo.save(m1)
        m2 = Matrix(
            id="world",
            created_at=datetime.now(),
        )
        repo.save(m2)

        dataset_repo = MatrixDataSetRepository()

        dataset = MatrixDataSet(
            name="some name",
            public=True,
            owner_id=user1.id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        matrix_relation = MatrixDataSetRelation(name="m1")
        matrix_relation.matrix_id = "hello"
        dataset.matrices.append(matrix_relation)
        matrix_relation = MatrixDataSetRelation(name="m2")
        matrix_relation.matrix_id = "world"
        dataset.matrices.append(matrix_relation)
        dataset_repo.save(dataset)

        dataset = MatrixDataSet(
            name="some name 2",
            public=False,
            owner_id=user2.id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        matrix_relation = MatrixDataSetRelation(name="m1")
        matrix_relation.matrix_id = "hello"
        dataset.matrices.append(matrix_relation)
        dataset_repo.save(dataset)

        res = dataset_repo.query("name 2")
        assert len(res) == 1
        assert len(res[0].matrices) == 1
        assert res[0].matrices[0].name == "m1"
        assert res[0].matrices[0].matrix.id == m1.id
        assert len(dataset_repo.query("name 2")) == 1
        assert len(dataset_repo.query("name")) == 2
        assert len(dataset_repo.query(None, user1.id)) == 1
        assert len(dataset_repo.query("name 2", user1.id)) == 0

        dataset_repo.delete(dataset.id)
        assert len(dataset_repo.query("name 2")) == 0
        assert repo.get(m1.id) is not None
        assert (
            len(
                db.session.query(MatrixDataSetRelation)
                .filter(MatrixDataSetRelation.dataset_id == dataset.id)
                .all()
            )
            == 0
        )
