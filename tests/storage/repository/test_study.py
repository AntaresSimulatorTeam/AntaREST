from datetime import datetime

from sqlalchemy.orm import Session  # type: ignore

from antarest.core.cache.business.local_chache import LocalCache
from antarest.core.model import PublicMode
from antarest.login.model import Group, User
from antarest.study.model import DEFAULT_WORKSPACE_NAME, RawStudy, Study, StudyContentStatus
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy


def test_lifecycle(db_session: Session) -> None:
    repo = StudyMetadataRepository(LocalCache(), session=db_session)

    user = User(id=1, name="admin")
    group = Group(id="my-group", name="group")

    a = Study(
        name="a",
        version="820",
        author="John Smith",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        public_mode=PublicMode.FULL,
        owner=user,
        groups=[group],
    )
    b = RawStudy(
        name="b",
        version="830",
        author="Morpheus",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        public_mode=PublicMode.FULL,
        owner=user,
        groups=[group],
    )
    c = RawStudy(
        name="c",
        version="830",
        author="Trinity",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        public_mode=PublicMode.FULL,
        owner=user,
        groups=[group],
        missing=datetime.utcnow(),
    )
    d = VariantStudy(
        name="d",
        version="830",
        author="Mr. Anderson",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        public_mode=PublicMode.FULL,
        owner=user,
        groups=[group],
    )

    a = repo.save(a)
    a_id = a.id

    repo.save(b)
    repo.save(c)
    repo.save(d)

    c = repo.one(a_id)
    assert a_id == c.id

    assert len(repo.get_all()) == 4
    assert len(repo.get_all_raw(exists=True)) == 1
    assert len(repo.get_all_raw(exists=False)) == 1
    assert len(repo.get_all_raw()) == 2

    repo.delete(a_id)
    assert repo.get(a_id) is None


def test_study_inheritance(db_session: Session) -> None:
    repo = StudyMetadataRepository(LocalCache(), session=db_session)

    user = User(id=0, name="admin")
    group = Group(id="my-group", name="group")
    a = RawStudy(
        name="a",
        version="820",
        author="John Smith",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        public_mode=PublicMode.FULL,
        owner=user,
        groups=[group],
        workspace=DEFAULT_WORKSPACE_NAME,
        path="study",
        content_status=StudyContentStatus.WARNING,
    )

    repo.save(a)
    b = repo.get(a.id)

    assert isinstance(b, RawStudy)
    assert b.path == "study"
