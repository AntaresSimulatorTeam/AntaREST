import uuid
from datetime import datetime

from sqlalchemy import create_engine

from antarest.common.persistence import Base
from antarest.storage.model import Metadata
from antarest.storage.repository.metadata import StudyMetadataRepository


def test_cyclelife():
    engine = create_engine("sqlite:///:memory:", echo=True)

    Base.metadata.create_all(engine)

    repo = StudyMetadataRepository(engine=engine)
    a = Metadata(
        name="a",
        version="42",
        author="John Smith",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    b = Metadata(
        name="b",
        version="43",
        author="Morpheus",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    a = repo.save(a)
    b = repo.save(b)
    assert b.id
    c = repo.get(a.id)
    assert a == c

    repo.delete(a.id)
    assert repo.get(a.id) is None
