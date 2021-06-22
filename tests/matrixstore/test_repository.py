from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

from sqlalchemy import create_engine

from antarest.common.config import Config, MatrixStoreConfig
from antarest.common.persistence import Base
from antarest.common.utils.fastapi_sqlalchemy import DBSessionMiddleware, db
from antarest.matrixstore.model import (
    Matrix,
    MatrixFreq,
    MatrixContent,
)
from antarest.matrixstore.repository import (
    MatrixRepository,
    MatrixContentRepository,
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
