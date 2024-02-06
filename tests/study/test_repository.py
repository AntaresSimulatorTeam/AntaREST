import datetime
import typing as t
from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session  # type: ignore

from antarest.core.interfaces.cache import ICache
from antarest.login.model import Group, User
from antarest.study.model import DEFAULT_WORKSPACE_NAME, RawStudy, Tag
from antarest.study.repository import StudyFilter, StudyMetadataRepository
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy
from tests.db_statement_recorder import DBStatementRecorder


@pytest.mark.parametrize(
    "managed, study_ids, exists, expected_ids",
    [
        (None, [], False, {"5", "6"}),
        (None, [], True, {"1", "2", "3", "4", "7", "8"}),
        (None, [], None, {"1", "2", "3", "4", "5", "6", "7", "8"}),
        (None, [1, 3, 5, 7], False, {"5"}),
        (None, [1, 3, 5, 7], True, {"1", "3", "7"}),
        (None, [1, 3, 5, 7], None, {"1", "3", "5", "7"}),
        (True, [], False, {"5"}),
        (True, [], True, {"1", "2", "3", "4", "8"}),
        (True, [], None, {"1", "2", "3", "4", "5", "8"}),
        (True, [1, 3, 5, 7], False, {"5"}),
        (True, [1, 3, 5, 7], True, {"1", "3"}),
        (True, [1, 3, 5, 7], None, {"1", "3", "5"}),
        (True, [2, 4, 6, 8], True, {"2", "4", "8"}),
        (True, [2, 4, 6, 8], None, {"2", "4", "8"}),
        (False, [], False, {"6"}),
        (False, [], True, {"7"}),
        (False, [], None, {"6", "7"}),
        (False, [1, 3, 5, 7], False, set()),
        (False, [1, 3, 5, 7], True, {"7"}),
        (False, [1, 3, 5, 7], None, {"7"}),
    ],
)
def test_repository_get_all__general_case(
    db_session: Session,
    managed: t.Union[bool, None],
    study_ids: t.List[str],
    exists: t.Union[bool, None],
    expected_ids: t.Set[str],
) -> None:
    test_workspace = "test-repository"
    icache: Mock = Mock(spec=ICache)
    repository = StudyMetadataRepository(cache_service=icache, session=db_session)

    study_1 = VariantStudy(id=1)
    study_2 = VariantStudy(id=2)
    study_3 = VariantStudy(id=3)
    study_4 = VariantStudy(id=4)
    study_5 = RawStudy(id=5, missing=datetime.datetime.now(), workspace=DEFAULT_WORKSPACE_NAME)
    study_6 = RawStudy(id=6, missing=datetime.datetime.now(), workspace=test_workspace)
    study_7 = RawStudy(id=7, missing=None, workspace=test_workspace)
    study_8 = RawStudy(id=8, missing=None, workspace=DEFAULT_WORKSPACE_NAME)

    db_session.add_all([study_1, study_2, study_3, study_4, study_5, study_6, study_7, study_8])
    db_session.commit()

    # use the db recorder to check that:
    # 1- retrieving all studies requires only 1 query
    # 2- accessing studies attributes does not require additional queries to db
    # 3- having an exact total of queries equals to 1
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(study_filter=StudyFilter(managed=managed, study_ids=study_ids, exists=exists))
        _ = [s.owner for s in all_studies]
        _ = [s.groups for s in all_studies]
        _ = [s.additional_data for s in all_studies]
        _ = [s.tags for s in all_studies]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)

    if expected_ids is not None:
        assert {s.id for s in all_studies} == expected_ids


def test_repository_get_all__incompatible_case(
    db_session: Session,
) -> None:
    test_workspace = "workspace1"
    icache: Mock = Mock(spec=ICache)
    repository = StudyMetadataRepository(cache_service=icache, session=db_session)

    study_1 = VariantStudy(id=1)
    study_2 = VariantStudy(id=2)
    study_3 = VariantStudy(id=3)
    study_4 = VariantStudy(id=4)
    study_5 = RawStudy(id=5, missing=datetime.datetime.now(), workspace=DEFAULT_WORKSPACE_NAME)
    study_6 = RawStudy(id=6, missing=datetime.datetime.now(), workspace=test_workspace)
    study_7 = RawStudy(id=7, missing=None, workspace=test_workspace)
    study_8 = RawStudy(id=8, missing=None, workspace=DEFAULT_WORKSPACE_NAME)

    db_session.add_all([study_1, study_2, study_3, study_4, study_5, study_6, study_7, study_8])
    db_session.commit()

    # case 1
    study_filter = StudyFilter(managed=False, variant=True)
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(study_filter=study_filter)
        _ = [s.owner for s in all_studies]
        _ = [s.groups for s in all_studies]
        _ = [s.additional_data for s in all_studies]
        _ = [s.tags for s in all_studies]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)
    assert not {s.id for s in all_studies}

    # case 2
    study_filter = StudyFilter(workspace=test_workspace, variant=True)
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(study_filter=study_filter)
        _ = [s.owner for s in all_studies]
        _ = [s.groups for s in all_studies]
        _ = [s.additional_data for s in all_studies]
        _ = [s.tags for s in all_studies]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)
    assert not {s.id for s in all_studies}

    # case 3
    study_filter = StudyFilter(exists=False, variant=True)
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(study_filter=study_filter)
        _ = [s.owner for s in all_studies]
        _ = [s.groups for s in all_studies]
        _ = [s.additional_data for s in all_studies]
        _ = [s.tags for s in all_studies]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)
    assert not {s.id for s in all_studies}


@pytest.mark.parametrize(
    "name, expected_ids",
    [
        ("", {"1", "2", "3", "4", "5", "6", "7", "8"}),
        ("specie", {"1", "2", "3", "4", "5", "6", "7", "8"}),
        ("prefix-specie", {"2", "3", "6", "7"}),
        ("variant", {"1", "2", "3", "4"}),
        ("variant-suffix", {"3", "4"}),
        ("raw", {"5", "6", "7", "8"}),
        ("raw-suffix", {"7", "8"}),
        ("prefix-variant", set()),
        ("specie-suffix", set()),
    ],
)
def test_repository_get_all__study_name_filter(
    db_session: Session,
    name: str,
    expected_ids: t.Set[str],
) -> None:
    icache: Mock = Mock(spec=ICache)
    repository = StudyMetadataRepository(cache_service=icache, session=db_session)

    study_1 = VariantStudy(id=1, name="specie-variant")
    study_2 = VariantStudy(id=2, name="prefix-specie-variant")
    study_3 = VariantStudy(id=3, name="prefix-specie-variant-suffix")
    study_4 = VariantStudy(id=4, name="specie-variant-suffix")
    study_5 = RawStudy(id=5, name="specie-raw")
    study_6 = RawStudy(id=6, name="prefix-specie-raw")
    study_7 = RawStudy(id=7, name="prefix-specie-raw-suffix")
    study_8 = RawStudy(id=8, name="specie-raw-suffix")

    db_session.add_all([study_1, study_2, study_3, study_4, study_5, study_6, study_7, study_8])
    db_session.commit()

    # use the db recorder to check that:
    # 1- retrieving all studies requires only 1 query
    # 2- accessing studies attributes does not require additional queries to db
    # 3- having an exact total of queries equals to 1
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(study_filter=StudyFilter(name=name))
        _ = [s.owner for s in all_studies]
        _ = [s.groups for s in all_studies]
        _ = [s.additional_data for s in all_studies]
        _ = [s.tags for s in all_studies]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)

    if expected_ids is not None:
        assert {s.id for s in all_studies} == expected_ids


@pytest.mark.parametrize(
    "managed, expected_ids",
    [
        (None, {"1", "2", "3", "4", "5", "6", "7", "8"}),
        (True, {"1", "2", "3", "4", "5", "8"}),
        (False, {"6", "7"}),
    ],
)
def test_repository_get_all__managed_study_filter(
    db_session: Session,
    managed: t.Optional[bool],
    expected_ids: t.Set[str],
) -> None:
    test_workspace = "test-workspace"
    icache: Mock = Mock(spec=ICache)
    repository = StudyMetadataRepository(cache_service=icache, session=db_session)

    study_1 = VariantStudy(id=1)
    study_2 = VariantStudy(id=2)
    study_3 = VariantStudy(id=3)
    study_4 = VariantStudy(id=4)
    study_5 = RawStudy(id=5, workspace=DEFAULT_WORKSPACE_NAME)
    study_6 = RawStudy(id=6, workspace=test_workspace)
    study_7 = RawStudy(id=7, workspace=test_workspace)
    study_8 = RawStudy(id=8, workspace=DEFAULT_WORKSPACE_NAME)

    db_session.add_all([study_1, study_2, study_3, study_4, study_5, study_6, study_7, study_8])
    db_session.commit()

    # use the db recorder to check that:
    # 1- retrieving all studies requires only 1 query
    # 2- accessing studies attributes does not require additional queries to db
    # 3- having an exact total of queries equals to 1
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(study_filter=StudyFilter(managed=managed))
        _ = [s.owner for s in all_studies]
        _ = [s.groups for s in all_studies]
        _ = [s.additional_data for s in all_studies]
        _ = [s.tags for s in all_studies]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)

    if expected_ids is not None:
        assert {s.id for s in all_studies} == expected_ids


@pytest.mark.parametrize(
    "archived, expected_ids",
    [
        (None, {"1", "2", "3", "4"}),
        (True, {"1", "3"}),
        (False, {"2", "4"}),
    ],
)
def test_repository_get_all__archived_study_filter(
    db_session: Session,
    archived: t.Optional[bool],
    expected_ids: t.Set[str],
) -> None:
    icache: Mock = Mock(spec=ICache)
    repository = StudyMetadataRepository(cache_service=icache, session=db_session)

    study_1 = VariantStudy(id=1, archived=True)
    study_2 = VariantStudy(id=2, archived=False)
    study_3 = RawStudy(id=3, archived=True)
    study_4 = RawStudy(id=4, archived=False)

    db_session.add_all([study_1, study_2, study_3, study_4])
    db_session.commit()

    # use the db recorder to check that:
    # 1- retrieving all studies requires only 1 query
    # 2- accessing studies attributes does not require additional queries to db
    # 3- having an exact total of queries equals to 1
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(study_filter=StudyFilter(archived=archived))
        _ = [s.owner for s in all_studies]
        _ = [s.groups for s in all_studies]
        _ = [s.additional_data for s in all_studies]
        _ = [s.tags for s in all_studies]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)

    if expected_ids is not None:
        assert {s.id for s in all_studies} == expected_ids


@pytest.mark.parametrize(
    "variant, expected_ids",
    [
        (None, {"1", "2", "3", "4"}),
        (True, {"1", "2"}),
        (False, {"3", "4"}),
    ],
)
def test_repository_get_all__variant_study_filter(
    db_session: Session,
    variant: t.Optional[bool],
    expected_ids: t.Set[str],
) -> None:
    icache: Mock = Mock(spec=ICache)
    repository = StudyMetadataRepository(cache_service=icache, session=db_session)

    study_1 = VariantStudy(id=1)
    study_2 = VariantStudy(id=2)
    study_3 = RawStudy(id=3)
    study_4 = RawStudy(id=4)

    db_session.add_all([study_1, study_2, study_3, study_4])
    db_session.commit()

    # use the db recorder to check that:
    # 1- retrieving all studies requires only 1 query
    # 2- accessing studies attributes does not require additional queries to db
    # 3- having an exact total of queries equals to 1
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(study_filter=StudyFilter(variant=variant))
        _ = [s.owner for s in all_studies]
        _ = [s.groups for s in all_studies]
        _ = [s.additional_data for s in all_studies]
        _ = [s.tags for s in all_studies]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)

    if expected_ids is not None:
        assert {s.id for s in all_studies} == expected_ids


@pytest.mark.parametrize(
    "versions, expected_ids",
    [
        ([], {"1", "2", "3", "4"}),
        (["1", "2"], {"1", "2", "3", "4"}),
        (["1"], {"1", "3"}),
        (["2"], {"2", "4"}),
        (["3"], set()),
    ],
)
def test_repository_get_all__study_version_filter(
    db_session: Session,
    versions: t.List[str],
    expected_ids: t.Set[str],
) -> None:
    icache: Mock = Mock(spec=ICache)
    repository = StudyMetadataRepository(cache_service=icache, session=db_session)

    study_1 = VariantStudy(id=1, version="1")
    study_2 = VariantStudy(id=2, version="2")
    study_3 = RawStudy(id=3, version="1")
    study_4 = RawStudy(id=4, version="2")

    db_session.add_all([study_1, study_2, study_3, study_4])
    db_session.commit()

    # use the db recorder to check that:
    # 1- retrieving all studies requires only 1 query
    # 2- accessing studies attributes does not require additional queries to db
    # 3- having an exact total of queries equals to 1
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(study_filter=StudyFilter(versions=versions))
        _ = [s.owner for s in all_studies]
        _ = [s.groups for s in all_studies]
        _ = [s.additional_data for s in all_studies]
        _ = [s.tags for s in all_studies]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)

    if expected_ids is not None:
        assert {s.id for s in all_studies} == expected_ids


@pytest.mark.parametrize(
    "users, expected_ids",
    [
        ([], {"1", "2", "3", "4"}),
        (["1000", "2000"], {"1", "2", "3", "4"}),
        (["1000"], {"1", "3"}),
        (["2000"], {"2", "4"}),
        (["3000"], set()),
    ],
)
def test_repository_get_all__study_users_filter(
    db_session: Session,
    users: t.List["int"],
    expected_ids: t.Set[str],
) -> None:
    icache: Mock = Mock(spec=ICache)
    repository = StudyMetadataRepository(cache_service=icache, session=db_session)

    test_user_1 = User(id=1000)
    test_user_2 = User(id=2000)

    study_1 = VariantStudy(id=1, owner=test_user_1)
    study_2 = VariantStudy(id=2, owner=test_user_2)
    study_3 = RawStudy(id=3, owner=test_user_1)
    study_4 = RawStudy(id=4, owner=test_user_2)

    db_session.add_all([test_user_1, test_user_2])
    db_session.commit()

    db_session.add_all([study_1, study_2, study_3, study_4])
    db_session.commit()

    # use the db recorder to check that:
    # 1- retrieving all studies requires only 1 query
    # 2- accessing studies attributes does not require additional queries to db
    # 3- having an exact total of queries equals to 1
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(study_filter=StudyFilter(users=users))
        _ = [s.owner for s in all_studies]
        _ = [s.groups for s in all_studies]
        _ = [s.additional_data for s in all_studies]
        _ = [s.tags for s in all_studies]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)

    if expected_ids is not None:
        assert {s.id for s in all_studies} == expected_ids


@pytest.mark.parametrize(
    "groups, expected_ids",
    [
        ([], {"1", "2", "3", "4"}),
        (["1000", "2000"], {"1", "2", "3", "4"}),
        (["1000"], {"1", "2", "4"}),
        (["2000"], {"2", "3"}),
        (["3000"], set()),
    ],
)
def test_repository_get_all__study_groups_filter(
    db_session: Session,
    groups: t.List[str],
    expected_ids: t.Set[str],
) -> None:
    icache: Mock = Mock(spec=ICache)
    repository = StudyMetadataRepository(cache_service=icache, session=db_session)

    test_group_1 = Group(id=1000)
    test_group_2 = Group(id=2000)

    study_1 = VariantStudy(id=1, groups=[test_group_1])
    study_2 = VariantStudy(id=2, groups=[test_group_1, test_group_2])
    study_3 = RawStudy(id=3, groups=[test_group_2])
    study_4 = RawStudy(id=4, groups=[test_group_1])

    db_session.add_all([test_group_1, test_group_2])
    db_session.commit()

    db_session.add_all([study_1, study_2, study_3, study_4])
    db_session.commit()

    # use the db recorder to check that:
    # 1- retrieving all studies requires only 1 query
    # 2- accessing studies attributes does not require additional queries to db
    # 3- having an exact total of queries equals to 1
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(study_filter=StudyFilter(groups=groups))
        _ = [s.owner for s in all_studies]
        _ = [s.groups for s in all_studies]
        _ = [s.additional_data for s in all_studies]
        _ = [s.tags for s in all_studies]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)

    if expected_ids is not None:
        assert {s.id for s in all_studies} == expected_ids


@pytest.mark.parametrize(
    "study_ids, expected_ids",
    [
        ([], {"1", "2", "3", "4"}),
        (["1", "2", "3", "4"], {"1", "2", "3", "4"}),
        (["1", "2", "4"], {"1", "2", "4"}),
        (["2", "3"], {"2", "3"}),
        (["2"], {"2"}),
        (["3000"], set()),
    ],
)
def test_repository_get_all__study_ids_filter(
    db_session: Session,
    study_ids: t.List[str],
    expected_ids: t.Set[str],
) -> None:
    icache: Mock = Mock(spec=ICache)
    repository = StudyMetadataRepository(cache_service=icache, session=db_session)

    study_1 = VariantStudy(id=1)
    study_2 = VariantStudy(id=2)
    study_3 = RawStudy(id=3)
    study_4 = RawStudy(id=4)

    db_session.add_all([study_1, study_2, study_3, study_4])
    db_session.commit()

    # use the db recorder to check that:
    # 1- retrieving all studies requires only 1 query
    # 2- accessing studies attributes does not require additional queries to db
    # 3- having an exact total of queries equals to 1
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(study_filter=StudyFilter(study_ids=study_ids))
        _ = [s.owner for s in all_studies]
        _ = [s.groups for s in all_studies]
        _ = [s.additional_data for s in all_studies]
        _ = [s.tags for s in all_studies]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)

    if expected_ids is not None:
        assert {s.id for s in all_studies} == expected_ids


@pytest.mark.parametrize(
    "exists, expected_ids",
    [
        (None, {"1", "2", "3", "4"}),
        (True, {"1", "2", "4"}),
        (False, {"3"}),
    ],
)
def test_repository_get_all__study_existence_filter(
    db_session: Session,
    exists: t.Optional[bool],
    expected_ids: t.Set[str],
) -> None:
    icache: Mock = Mock(spec=ICache)
    repository = StudyMetadataRepository(cache_service=icache, session=db_session)

    study_1 = VariantStudy(id=1)
    study_2 = VariantStudy(id=2)
    study_3 = RawStudy(id=3, missing=datetime.datetime.now())
    study_4 = RawStudy(id=4)

    db_session.add_all([study_1, study_2, study_3, study_4])
    db_session.commit()

    # use the db recorder to check that:
    # 1- retrieving all studies requires only 1 query
    # 2- accessing studies attributes does not require additional queries to db
    # 3- having an exact total of queries equals to 1
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(study_filter=StudyFilter(exists=exists))
        _ = [s.owner for s in all_studies]
        _ = [s.groups for s in all_studies]
        _ = [s.additional_data for s in all_studies]
        _ = [s.tags for s in all_studies]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)

    if expected_ids is not None:
        assert {s.id for s in all_studies} == expected_ids


@pytest.mark.parametrize(
    "workspace, expected_ids",
    [
        ("", {"1", "2", "3", "4"}),
        ("workspace-1", {"3"}),
        ("workspace-2", {"4"}),
        ("workspace-3", set()),
    ],
)
def test_repository_get_all__study_workspace_filter(
    db_session: Session,
    workspace: str,
    expected_ids: t.Set[str],
) -> None:
    icache: Mock = Mock(spec=ICache)
    repository = StudyMetadataRepository(cache_service=icache, session=db_session)

    study_1 = VariantStudy(id=1)
    study_2 = VariantStudy(id=2)
    study_3 = RawStudy(id=3, workspace="workspace-1")
    study_4 = RawStudy(id=4, workspace="workspace-2")

    db_session.add_all([study_1, study_2, study_3, study_4])
    db_session.commit()

    # use the db recorder to check that:
    # 1- retrieving all studies requires only 1 query
    # 2- accessing studies attributes does not require additional queries to db
    # 3- having an exact total of queries equals to 1
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(study_filter=StudyFilter(workspace=workspace))
        _ = [s.owner for s in all_studies]
        _ = [s.groups for s in all_studies]
        _ = [s.additional_data for s in all_studies]
        _ = [s.tags for s in all_studies]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)

    if expected_ids is not None:
        assert {s.id for s in all_studies} == expected_ids


@pytest.mark.parametrize(
    "folder, expected_ids",
    [
        ("", {"1", "2", "3", "4"}),
        ("/home/folder-", {"1", "2", "3", "4"}),
        ("/home/folder-1", {"1", "3"}),
        ("/home/folder-2", {"2", "4"}),
        ("/home/folder-3", set()),
        ("folder-1", set()),
    ],
)
def test_repository_get_all__study_folder_filter(
    db_session: Session,
    folder: str,
    expected_ids: t.Set[str],
) -> None:
    icache: Mock = Mock(spec=ICache)
    repository = StudyMetadataRepository(cache_service=icache, session=db_session)

    study_1 = VariantStudy(id=1, folder="/home/folder-1")
    study_2 = VariantStudy(id=2, folder="/home/folder-2")
    study_3 = RawStudy(id=3, folder="/home/folder-1")
    study_4 = RawStudy(id=4, folder="/home/folder-2")

    db_session.add_all([study_1, study_2, study_3, study_4])
    db_session.commit()

    # use the db recorder to check that:
    # 1- retrieving all studies requires only 1 query
    # 2- accessing studies attributes does not require additional queries to db
    # 3- having an exact total of queries equals to 1
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(study_filter=StudyFilter(folder=folder))
        _ = [s.owner for s in all_studies]
        _ = [s.groups for s in all_studies]
        _ = [s.additional_data for s in all_studies]
        _ = [s.tags for s in all_studies]

    assert len(db_recorder.sql_statements) == 1, str(db_recorder)

    if expected_ids is not None:
        assert {s.id for s in all_studies} == expected_ids


@pytest.mark.parametrize(
    "tags, expected_ids",
    [
        ([], {"1", "2", "3", "4", "5", "6", "7", "8"}),
        (["decennial"], {"2", "4", "6", "8"}),
        (["winter_transition"], {"3", "4", "7", "8"}),
        (["decennial", "winter_transition"], {"2", "3", "4", "6", "7", "8"}),
        (["no-study-tag"], set()),
    ],
)
def test_repository_get_all__study_tags_filter(
    db_session: Session,
    tags: t.List[str],
    expected_ids: t.Set[str],
) -> None:
    icache: Mock = Mock(spec=ICache)
    repository = StudyMetadataRepository(cache_service=icache, session=db_session)

    test_tag_1 = Tag(label="hidden-tag")
    test_tag_2 = Tag(label="decennial")
    test_tag_3 = Tag(label="winter_transition")

    study_1 = VariantStudy(id=1, tags=[test_tag_1])
    study_2 = VariantStudy(id=2, tags=[test_tag_2])
    study_3 = VariantStudy(id=3, tags=[test_tag_3])
    study_4 = VariantStudy(id=4, tags=[test_tag_2, test_tag_3])
    study_5 = RawStudy(id=5, tags=[test_tag_1])
    study_6 = RawStudy(id=6, tags=[test_tag_2])
    study_7 = RawStudy(id=7, tags=[test_tag_3])
    study_8 = RawStudy(id=8, tags=[test_tag_2, test_tag_3])

    db_session.add_all([study_1, study_2, study_3, study_4, study_5, study_6, study_7, study_8])
    db_session.commit()

    # use the db recorder to check that:
    # 1- retrieving all studies requires only 1 query
    # 2- accessing studies attributes does not require additional queries to db
    # 3- having an exact total of queries equals to 1
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(study_filter=StudyFilter(tags=tags))
        _ = [s.owner for s in all_studies]
        _ = [s.groups for s in all_studies]
        _ = [s.additional_data for s in all_studies]
        _ = [s.tags for s in all_studies]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)

    if expected_ids is not None:
        assert {s.id for s in all_studies} == expected_ids
