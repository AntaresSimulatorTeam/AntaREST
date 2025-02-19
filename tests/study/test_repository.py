# Copyright (c) 2025, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import datetime
import typing as t
from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session  # type: ignore

from antarest.core.interfaces.cache import ICache
from antarest.core.model import PublicMode
from antarest.login.model import Group, User
from antarest.study.model import DEFAULT_WORKSPACE_NAME, RawStudy, Tag
from antarest.study.repository import (
    AccessPermissions,
    StudyFilter,
    StudyMetadataRepository,
    StudyPagination,
    StudySortBy,
)
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy
from tests.db_statement_recorder import DBStatementRecorder


@pytest.mark.parametrize(
    "managed, study_names, exists, expected_names",
    [
        (None, [], False, ["s5", "s6"]),
        (None, [], True, ["s1", "s2", "s3", "s4", "s7", "s8"]),
        (None, [], None, ["s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8"]),
        (None, ["s1", "s3", "s5", "s7"], False, ["s5"]),
        (None, ["s1", "s3", "s5", "s7"], True, ["s1", "s3", "s7"]),
        (None, ["s1", "s3", "s5", "s7"], None, ["s1", "s3", "s5", "s7"]),
        (True, [], False, ["s5"]),
        (True, [], True, ["s1", "s2", "s3", "s4", "s8"]),
        (True, [], None, ["s1", "s2", "s3", "s4", "s5", "s8"]),
        (True, ["s1", "s3", "s5", "s7"], False, ["s5"]),
        (True, ["s1", "s3", "s5", "s7"], True, ["s1", "s3"]),
        (True, ["s1", "s3", "s5", "s7"], None, ["s1", "s3", "s5"]),
        (True, ["s2", "s4", "s6", "s8"], True, ["s2", "s4", "s8"]),
        (True, ["s2", "s4", "s6", "s8"], None, ["s2", "s4", "s8"]),
        (False, [], False, ["s6"]),
        (False, [], True, ["s7"]),
        (False, [], None, ["s6", "s7"]),
        (False, ["s1", "s3", "s5", "s7"], False, []),
        (False, ["s1", "s3", "s5", "s7"], True, ["s7"]),
        (False, ["s1", "s3", "s5", "s7"], None, ["s7"]),
    ],
)
def test_get_all__general_case(
    db_session: Session,
    managed: t.Union[bool, None],
    study_names: t.Sequence[str],
    exists: t.Union[bool, None],
    expected_names: t.Sequence[str],
) -> None:
    test_workspace = "test-repository"
    icache: Mock = Mock(spec=ICache)
    repository = StudyMetadataRepository(cache_service=icache, session=db_session)

    study_1 = VariantStudy(name="s1")
    study_2 = VariantStudy(name="s2")
    study_3 = VariantStudy(name="s3")
    study_4 = VariantStudy(name="s4")
    study_5 = RawStudy(name="s5", missing=datetime.datetime.now(), workspace=DEFAULT_WORKSPACE_NAME)
    study_6 = RawStudy(name="s6", missing=datetime.datetime.now(), workspace=test_workspace)
    study_7 = RawStudy(name="s7", missing=None, workspace=test_workspace)
    study_8 = RawStudy(name="s8", missing=None, workspace=DEFAULT_WORKSPACE_NAME)

    my_studies = [study_1, study_2, study_3, study_4, study_5, study_6, study_7, study_8]
    db_session.add_all(my_studies)
    db_session.commit()

    ids_by_names = {s.name: s.id for s in my_studies}

    # use the db recorder to check that:
    # 1- retrieving all studies requires only 1 query
    # 2- accessing studies attributes does not require additional queries to db
    # 3- having an exact total of queries equals to 1
    study_filter = StudyFilter(
        managed=managed,
        study_ids=[ids_by_names[name] for name in study_names],
        exists=exists,
        access_permissions=AccessPermissions(is_admin=True),
    )
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(
            study_filter=study_filter,
            sort_by=StudySortBy.NAME_ASC,
        )
        _ = [s.owner for s in all_studies]
        _ = [s.groups for s in all_studies]
        _ = [s.additional_data for s in all_studies]
        _ = [s.tags for s in all_studies]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)

    # test that the expected studies are returned
    assert [s.name for s in all_studies] == expected_names

    # -- test pagination
    page_nb = 1
    page_size = 2
    page_slice = slice(page_nb * page_size, (page_nb + 1) * page_size)

    # test pagination in normal order
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(
            study_filter=study_filter,
            sort_by=StudySortBy.NAME_ASC,
            pagination=StudyPagination(page_nb=page_nb, page_size=page_size),
        )
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)
    assert [s.name for s in all_studies] == expected_names[page_slice]

    # test pagination in reverse order
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(
            study_filter=study_filter,
            sort_by=StudySortBy.NAME_DESC,
            pagination=StudyPagination(page_nb=page_nb, page_size=page_size),
        )
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)
    assert [s.name for s in all_studies] == expected_names[::-1][page_slice]


def test_get_all__incompatible_case(
    db_session: Session,
) -> None:
    test_workspace = "workspace1"
    icache: Mock = Mock(spec=ICache)
    repository = StudyMetadataRepository(cache_service=icache, session=db_session)

    study_1 = VariantStudy(id=1, name="study-1")
    study_2 = VariantStudy(id=2, name="study-2")
    study_3 = VariantStudy(id=3, name="study-3")
    study_4 = VariantStudy(id=4, name="study-4")
    study_5 = RawStudy(id=5, name="study-5", missing=datetime.datetime.now(), workspace=DEFAULT_WORKSPACE_NAME)
    study_6 = RawStudy(id=6, name="study-6", missing=datetime.datetime.now(), workspace=test_workspace)
    study_7 = RawStudy(id=7, name="study-7", missing=None, workspace=test_workspace)
    study_8 = RawStudy(id=8, name="study-8", missing=None, workspace=DEFAULT_WORKSPACE_NAME)

    db_session.add_all([study_1, study_2, study_3, study_4, study_5, study_6, study_7, study_8])
    db_session.commit()

    # case 1
    study_filter = StudyFilter(managed=False, variant=True, access_permissions=AccessPermissions(is_admin=True))
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(study_filter=study_filter)
        _ = [s.owner for s in all_studies]
        _ = [s.groups for s in all_studies]
        _ = [s.additional_data for s in all_studies]
        _ = [s.tags for s in all_studies]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)
    assert not {s.id for s in all_studies}

    # case 2
    study_filter = StudyFilter(
        workspace=test_workspace, variant=True, access_permissions=AccessPermissions(is_admin=True)
    )
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(study_filter=study_filter)
        _ = [s.owner for s in all_studies]
        _ = [s.groups for s in all_studies]
        _ = [s.additional_data for s in all_studies]
        _ = [s.tags for s in all_studies]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)
    assert not {s.id for s in all_studies}

    # case 3
    study_filter = StudyFilter(exists=False, variant=True, access_permissions=AccessPermissions(is_admin=True))
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
        ("", ["1", "2", "3", "4", "5", "6", "7", "8"]),
        ("specie", ["1", "2", "3", "4", "5", "6", "7", "8"]),
        ("prefix-specie", ["2", "3", "6", "7"]),
        ("variant", ["1", "2", "3", "4"]),
        ("variant-suffix", ["3", "4"]),
        ("raw", ["5", "6", "7", "8"]),
        ("raw-suffix", ["7", "8"]),
        ("prefix-variant", []),
        ("specie-suffix", []),
    ],
)
def test_get_all__study_name_filter(
    db_session: Session,
    name: str,
    expected_ids: t.List[str],
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

    mapping_ids_names = {
        str(s.id): s.name for s in [study_1, study_2, study_3, study_4, study_5, study_6, study_7, study_8]
    }

    db_session.add_all([study_1, study_2, study_3, study_4, study_5, study_6, study_7, study_8])
    db_session.commit()

    # use the db recorder to check that:
    # 1- retrieving all studies requires only 1 query
    # 2- accessing studies attributes does not require additional queries to db
    # 3- having an exact total of queries equals to 1
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(
            study_filter=StudyFilter(name=name, access_permissions=AccessPermissions(is_admin=True))
        )
        _ = [s.owner for s in all_studies]
        _ = [s.groups for s in all_studies]
        _ = [s.additional_data for s in all_studies]
        _ = [s.tags for s in all_studies]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)

    if expected_ids is not None:
        assert sorted(s.id for s in all_studies) == expected_ids

    # test pagination
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(
            study_filter=StudyFilter(name=name, access_permissions=AccessPermissions(is_admin=True)),
            pagination=StudyPagination(page_nb=1, page_size=2),
        )
        assert len(all_studies) == max(0, min(len(expected_ids) - 2, 2))
        name_sorted_expected_studies = sorted(expected_ids, key=lambda s_id: mapping_ids_names[s_id])
        assert sorted(s.id for s in all_studies) == name_sorted_expected_studies[2:4]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)


@pytest.mark.parametrize(
    "managed, expected_ids",
    [
        (None, ["1", "2", "3", "4", "5", "6", "7", "8"]),
        (True, ["1", "2", "3", "4", "5", "8"]),
        (False, ["6", "7"]),
    ],
)
def test_get_all__managed_study_filter(
    db_session: Session,
    managed: t.Optional[bool],
    expected_ids: t.List[str],
) -> None:
    test_workspace = "test-workspace"
    icache: Mock = Mock(spec=ICache)
    repository = StudyMetadataRepository(cache_service=icache, session=db_session)

    study_1 = VariantStudy(id=1, name="study-1")
    study_2 = VariantStudy(id=2, name="study-2")
    study_3 = VariantStudy(id=3, name="study-3")
    study_4 = VariantStudy(id=4, name="study-4")
    study_5 = RawStudy(id=5, name="study-5", workspace=DEFAULT_WORKSPACE_NAME)
    study_6 = RawStudy(id=6, name="study-6", workspace=test_workspace)
    study_7 = RawStudy(id=7, name="study-7", workspace=test_workspace)
    study_8 = RawStudy(id=8, name="study-8", workspace=DEFAULT_WORKSPACE_NAME)

    db_session.add_all([study_1, study_2, study_3, study_4, study_5, study_6, study_7, study_8])
    db_session.commit()

    # use the db recorder to check that:
    # 1- retrieving all studies requires only 1 query
    # 2- accessing studies attributes does not require additional queries to db
    # 3- having an exact total of queries equals to 1
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(
            study_filter=StudyFilter(managed=managed, access_permissions=AccessPermissions(is_admin=True))
        )
        _ = [s.owner for s in all_studies]
        _ = [s.groups for s in all_studies]
        _ = [s.additional_data for s in all_studies]
        _ = [s.tags for s in all_studies]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)

    if expected_ids is not None:
        assert sorted(s.id for s in all_studies) == expected_ids

    # test pagination
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(
            study_filter=StudyFilter(managed=managed, access_permissions=AccessPermissions(is_admin=True)),
            pagination=StudyPagination(page_nb=1, page_size=2),
        )
        assert len(all_studies) == max(0, min(len(expected_ids) - 2, 2))
        assert sorted(s.id for s in all_studies) == expected_ids[2:4]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)


@pytest.mark.parametrize(
    "archived, expected_ids",
    [
        (None, ["1", "2", "3", "4"]),
        (True, ["1", "3"]),
        (False, ["2", "4"]),
    ],
)
def test_get_all__archived_study_filter(
    db_session: Session,
    archived: t.Optional[bool],
    expected_ids: t.List[str],
) -> None:
    icache: Mock = Mock(spec=ICache)
    repository = StudyMetadataRepository(cache_service=icache, session=db_session)

    study_1 = VariantStudy(id=1, name="study-1", archived=True)
    study_2 = VariantStudy(id=2, name="study-2", archived=False)
    study_3 = RawStudy(id=3, name="study-3", archived=True)
    study_4 = RawStudy(id=4, name="study-4", archived=False)

    db_session.add_all([study_1, study_2, study_3, study_4])
    db_session.commit()

    # use the db recorder to check that:
    # 1- retrieving all studies requires only 1 query
    # 2- accessing studies attributes does not require additional queries to db
    # 3- having an exact total of queries equals to 1
    study_filter = StudyFilter(archived=archived, access_permissions=AccessPermissions(is_admin=True))
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(study_filter=study_filter)
        _ = [s.owner for s in all_studies]
        _ = [s.groups for s in all_studies]
        _ = [s.additional_data for s in all_studies]
        _ = [s.tags for s in all_studies]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)

    if expected_ids is not None:
        assert sorted(s.id for s in all_studies) == expected_ids

    # test pagination
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(
            study_filter=study_filter,
            pagination=StudyPagination(page_nb=1, page_size=1),
        )
        assert len(all_studies) == max(0, min(len(expected_ids) - 1, 1))
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)


@pytest.mark.parametrize(
    "variant, expected_ids",
    [
        (None, ["1", "2", "3", "4"]),
        (True, ["1", "2"]),
        (False, ["3", "4"]),
    ],
)
def test_get_all__variant_study_filter(
    db_session: Session,
    variant: t.Optional[bool],
    expected_ids: t.List[str],
) -> None:
    icache: Mock = Mock(spec=ICache)
    repository = StudyMetadataRepository(cache_service=icache, session=db_session)

    study_1 = VariantStudy(id=1, name="study-1")
    study_2 = VariantStudy(id=2, name="study-2")
    study_3 = RawStudy(id=3, name="study-3")
    study_4 = RawStudy(id=4, name="study-4")

    db_session.add_all([study_1, study_2, study_3, study_4])
    db_session.commit()

    # use the db recorder to check that:
    # 1- retrieving all studies requires only 1 query
    # 2- accessing studies attributes does not require additional queries to db
    # 3- having an exact total of queries equals to 1
    study_filter = StudyFilter(variant=variant, access_permissions=AccessPermissions(is_admin=True))
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(study_filter=study_filter)
        _ = [s.owner for s in all_studies]
        _ = [s.groups for s in all_studies]
        _ = [s.additional_data for s in all_studies]
        _ = [s.tags for s in all_studies]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)

    if expected_ids is not None:
        assert sorted(s.id for s in all_studies) == expected_ids

    # test pagination
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(
            study_filter=study_filter,
            pagination=StudyPagination(page_nb=1, page_size=1),
        )
        assert len(all_studies) == max(0, min(len(expected_ids) - 1, 1))
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)


@pytest.mark.parametrize(
    "versions, expected_ids",
    [
        ([], ["1", "2", "3", "4"]),
        (["1", "2"], ["1", "2", "3", "4"]),
        (["1"], ["1", "3"]),
        (["2"], ["2", "4"]),
        (["3"], []),
    ],
)
def test_get_all__study_version_filter(
    db_session: Session,
    versions: t.Sequence[str],
    expected_ids: t.List[str],
) -> None:
    icache: Mock = Mock(spec=ICache)
    repository = StudyMetadataRepository(cache_service=icache, session=db_session)

    study_1 = VariantStudy(id=1, name="study-1", version="1")
    study_2 = VariantStudy(id=2, name="study-2", version="2")
    study_3 = RawStudy(id=3, name="study-3", version="1")
    study_4 = RawStudy(id=4, name="study-4", version="2")

    db_session.add_all([study_1, study_2, study_3, study_4])
    db_session.commit()

    # use the db recorder to check that:
    # 1- retrieving all studies requires only 1 query
    # 2- accessing studies attributes does not require additional queries to db
    # 3- having an exact total of queries equals to 1
    study_filter = StudyFilter(versions=versions, access_permissions=AccessPermissions(is_admin=True))
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(study_filter=study_filter)
        _ = [s.owner for s in all_studies]
        _ = [s.groups for s in all_studies]
        _ = [s.additional_data for s in all_studies]
        _ = [s.tags for s in all_studies]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)

    if expected_ids is not None:
        assert sorted(s.id for s in all_studies) == expected_ids

    # test pagination
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(
            study_filter=study_filter,
            pagination=StudyPagination(page_nb=1, page_size=1),
        )
        assert len(all_studies) == max(0, min(len(expected_ids) - 1, 1))
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)


@pytest.mark.parametrize(
    "users, expected_ids",
    [
        ([], ["1", "2", "3", "4"]),
        (["1000", "2000"], ["1", "2", "3", "4"]),
        (["1000"], ["1", "3"]),
        (["2000"], ["2", "4"]),
        (["3000"], []),
    ],
)
def test_get_all__study_users_filter(
    db_session: Session,
    users: t.Sequence["int"],
    expected_ids: t.List[str],
) -> None:
    icache: Mock = Mock(spec=ICache)
    repository = StudyMetadataRepository(cache_service=icache, session=db_session)

    test_user_1 = User(id=1000)
    test_user_2 = User(id=2000)

    study_1 = VariantStudy(id=1, name="study-1", owner=test_user_1)
    study_2 = VariantStudy(id=2, name="study-2", owner=test_user_2)
    study_3 = RawStudy(id=3, name="study-3", owner=test_user_1)
    study_4 = RawStudy(id=4, name="study-4", owner=test_user_2)

    db_session.add_all([test_user_1, test_user_2])
    db_session.commit()

    db_session.add_all([study_1, study_2, study_3, study_4])
    db_session.commit()

    # use the db recorder to check that:
    # 1- retrieving all studies requires only 1 query
    # 2- accessing studies attributes does not require additional queries to db
    # 3- having an exact total of queries equals to 1
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(
            study_filter=StudyFilter(users=users, access_permissions=AccessPermissions(is_admin=True))
        )
        _ = [s.owner for s in all_studies]
        _ = [s.groups for s in all_studies]
        _ = [s.additional_data for s in all_studies]
        _ = [s.tags for s in all_studies]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)

    if expected_ids is not None:
        assert sorted(s.id for s in all_studies) == expected_ids

    # test pagination
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(
            study_filter=StudyFilter(users=users, access_permissions=AccessPermissions(is_admin=True)),
            pagination=StudyPagination(page_nb=1, page_size=2),
        )
        assert len(all_studies) == max(0, min(len(expected_ids) - 2, 2))
        assert sorted(s.id for s in all_studies) == expected_ids[2:4]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)


@pytest.mark.parametrize(
    "groups, expected_ids",
    [
        ([], ["1", "2", "3", "4"]),
        (["1000", "2000"], ["1", "2", "3", "4"]),
        (["1000"], ["1", "2", "4"]),
        (["2000"], ["2", "3"]),
        (["3000"], []),
    ],
)
def test_get_all__study_groups_filter(
    db_session: Session,
    groups: t.Sequence[str],
    expected_ids: t.List[str],
) -> None:
    icache: Mock = Mock(spec=ICache)
    repository = StudyMetadataRepository(cache_service=icache, session=db_session)

    test_group_1 = Group(id=1000)
    test_group_2 = Group(id=2000)

    study_1 = VariantStudy(id=1, name="study-1", groups=[test_group_1])
    study_2 = VariantStudy(id=2, name="study-2", groups=[test_group_1, test_group_2])
    study_3 = RawStudy(id=3, name="study-3", groups=[test_group_2])
    study_4 = RawStudy(id=4, name="study-4", groups=[test_group_1])

    db_session.add_all([test_group_1, test_group_2])
    db_session.commit()

    db_session.add_all([study_1, study_2, study_3, study_4])
    db_session.commit()

    # use the db recorder to check that:
    # 1- retrieving all studies requires only 1 query
    # 2- accessing studies attributes does not require additional queries to db
    # 3- having an exact total of queries equals to 1
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(
            study_filter=StudyFilter(groups=groups, access_permissions=AccessPermissions(is_admin=True))
        )
        _ = [s.owner for s in all_studies]
        _ = [s.groups for s in all_studies]
        _ = [s.additional_data for s in all_studies]
        _ = [s.tags for s in all_studies]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)

    if expected_ids is not None:
        assert sorted(s.id for s in all_studies) == expected_ids

    # test pagination
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(
            study_filter=StudyFilter(groups=groups, access_permissions=AccessPermissions(is_admin=True)),
            pagination=StudyPagination(page_nb=1, page_size=2),
        )
        assert len(all_studies) == max(0, min(len(expected_ids) - 2, 2))
        assert sorted(s.id for s in all_studies) == expected_ids[2:4]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)


@pytest.mark.parametrize(
    "study_ids, expected_ids",
    [
        ([], ["1", "2", "3", "4"]),
        (["1", "2", "3", "4"], ["1", "2", "3", "4"]),
        (["1", "2", "4"], ["1", "2", "4"]),
        (["2", "3"], ["2", "3"]),
        (["2"], ["2"]),
        (["3000"], []),
    ],
)
def test_get_all__study_ids_filter(
    db_session: Session,
    study_ids: t.Sequence[str],
    expected_ids: t.List[str],
) -> None:
    icache: Mock = Mock(spec=ICache)
    repository = StudyMetadataRepository(cache_service=icache, session=db_session)

    study_1 = VariantStudy(id=1, name="study-1")
    study_2 = VariantStudy(id=2, name="study-2")
    study_3 = RawStudy(id=3, name="study-3")
    study_4 = RawStudy(id=4, name="study-4")

    db_session.add_all([study_1, study_2, study_3, study_4])
    db_session.commit()

    # use the db recorder to check that:
    # 1- retrieving all studies requires only 1 query
    # 2- accessing studies attributes does not require additional queries to db
    # 3- having an exact total of queries equals to 1
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(
            study_filter=StudyFilter(study_ids=study_ids, access_permissions=AccessPermissions(is_admin=True))
        )
        _ = [s.owner for s in all_studies]
        _ = [s.groups for s in all_studies]
        _ = [s.additional_data for s in all_studies]
        _ = [s.tags for s in all_studies]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)

    if expected_ids is not None:
        assert sorted(s.id for s in all_studies) == expected_ids

    # test pagination
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(
            study_filter=StudyFilter(study_ids=study_ids, access_permissions=AccessPermissions(is_admin=True)),
            pagination=StudyPagination(page_nb=1, page_size=2),
        )
        assert len(all_studies) == max(0, min(len(expected_ids) - 2, 2))
        assert sorted(s.id for s in all_studies) == expected_ids[2:4]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)


@pytest.mark.parametrize(
    "exists, expected_ids",
    [
        (None, ["1", "2", "3", "4"]),
        (True, ["1", "2", "4"]),
        (False, ["3"]),
    ],
)
def test_get_all__study_existence_filter(
    db_session: Session,
    exists: t.Optional[bool],
    expected_ids: t.List[str],
) -> None:
    icache: Mock = Mock(spec=ICache)
    repository = StudyMetadataRepository(cache_service=icache, session=db_session)

    study_1 = VariantStudy(id=1, name="study-1")
    study_2 = VariantStudy(id=2, name="study-2")
    study_3 = RawStudy(id=3, name="study-3", missing=datetime.datetime.now())
    study_4 = RawStudy(id=4, name="study-4")

    db_session.add_all([study_1, study_2, study_3, study_4])
    db_session.commit()

    # use the db recorder to check that:
    # 1- retrieving all studies requires only 1 query
    # 2- accessing studies attributes does not require additional queries to db
    # 3- having an exact total of queries equals to 1
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(
            study_filter=StudyFilter(exists=exists, access_permissions=AccessPermissions(is_admin=True))
        )
        _ = [s.owner for s in all_studies]
        _ = [s.groups for s in all_studies]
        _ = [s.additional_data for s in all_studies]
        _ = [s.tags for s in all_studies]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)

    if expected_ids is not None:
        assert sorted(s.id for s in all_studies) == expected_ids

    # test pagination
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(
            study_filter=StudyFilter(exists=exists, access_permissions=AccessPermissions(is_admin=True)),
            pagination=StudyPagination(page_nb=1, page_size=2),
        )
        assert len(all_studies) == max(0, min(len(expected_ids) - 2, 2))
        assert sorted(s.id for s in all_studies) == expected_ids[2:4]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)


@pytest.mark.parametrize(
    "workspace, expected_ids",
    [
        ("", ["1", "2", "3", "4"]),
        ("workspace-1", ["3"]),
        ("workspace-2", ["4"]),
        ("workspace-3", []),
    ],
)
def test_get_all__study_workspace_filter(
    db_session: Session,
    workspace: str,
    expected_ids: t.List[str],
) -> None:
    icache: Mock = Mock(spec=ICache)
    repository = StudyMetadataRepository(cache_service=icache, session=db_session)

    study_1 = VariantStudy(id=1, name="study-1")
    study_2 = VariantStudy(id=2, name="study-2")
    study_3 = RawStudy(id=3, name="study-3", workspace="workspace-1")
    study_4 = RawStudy(id=4, name="study-4", workspace="workspace-2")

    db_session.add_all([study_1, study_2, study_3, study_4])
    db_session.commit()

    # use the db recorder to check that:
    # 1- retrieving all studies requires only 1 query
    # 2- accessing studies attributes does not require additional queries to db
    # 3- having an exact total of queries equals to 1
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(
            study_filter=StudyFilter(workspace=workspace, access_permissions=AccessPermissions(is_admin=True))
        )
        _ = [s.owner for s in all_studies]
        _ = [s.groups for s in all_studies]
        _ = [s.additional_data for s in all_studies]
        _ = [s.tags for s in all_studies]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)

    if expected_ids is not None:
        assert sorted(s.id for s in all_studies) == expected_ids

    # test pagination
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(
            study_filter=StudyFilter(workspace=workspace, access_permissions=AccessPermissions(is_admin=True)),
            pagination=StudyPagination(page_nb=1, page_size=2),
        )
        assert len(all_studies) == max(0, min(len(expected_ids) - 2, 2))
        assert sorted(s.id for s in all_studies) == expected_ids[2:4]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)


@pytest.mark.parametrize(
    "folder, expected_ids",
    [
        ("", ["1", "2", "3", "4"]),
        ("/home/folder-", ["1", "2", "3", "4"]),
        ("/home/folder-1", ["1", "3"]),
        ("/home/folder-2", ["2", "4"]),
        ("/home/folder-3", []),
        ("folder-1", []),
    ],
)
def test_get_all__study_folder_filter(
    db_session: Session,
    folder: str,
    expected_ids: t.List[str],
) -> None:
    icache: Mock = Mock(spec=ICache)
    repository = StudyMetadataRepository(cache_service=icache, session=db_session)

    study_1 = VariantStudy(id=1, name="study-1", folder="/home/folder-1")
    study_2 = VariantStudy(id=2, name="study-2", folder="/home/folder-2")
    study_3 = RawStudy(id=3, name="study-3", folder="/home/folder-1")
    study_4 = RawStudy(id=4, name="study-4", folder="/home/folder-2")

    db_session.add_all([study_1, study_2, study_3, study_4])
    db_session.commit()

    # use the db recorder to check that:
    # 1- retrieving all studies requires only 1 query
    # 2- accessing studies attributes does not require additional queries to db
    # 3- having an exact total of queries equals to 1
    study_filter = StudyFilter(folder=folder, access_permissions=AccessPermissions(is_admin=True))
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(study_filter=study_filter)
        _ = [s.owner for s in all_studies]
        _ = [s.groups for s in all_studies]
        _ = [s.additional_data for s in all_studies]
        _ = [s.tags for s in all_studies]

    assert len(db_recorder.sql_statements) == 1, str(db_recorder)

    if expected_ids is not None:
        assert sorted(s.id for s in all_studies) == expected_ids

    # test pagination
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(
            study_filter=study_filter,
            pagination=StudyPagination(page_nb=1, page_size=1),
        )
        assert len(all_studies) == max(0, min(len(expected_ids) - 1, 1))
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)


@pytest.mark.parametrize(
    "tags, expected_ids",
    [
        ([], ["1", "2", "3", "4", "5", "6", "7", "8"]),
        (["decennial"], ["2", "4", "6", "8"]),
        (["winter_transition"], ["3", "4", "7", "8"]),
        (["decennial", "winter_transition"], ["2", "3", "4", "6", "7", "8"]),
        (["no-study-tag"], []),
    ],
)
def test_get_all__study_tags_filter(
    db_session: Session,
    tags: t.Sequence[str],
    expected_ids: t.List[str],
) -> None:
    icache: Mock = Mock(spec=ICache)
    repository = StudyMetadataRepository(cache_service=icache, session=db_session)

    test_tag_1 = Tag(label="hidden-tag")
    test_tag_2 = Tag(label="decennial")
    test_tag_3 = Tag(label="Winter_Transition")  # note the different case

    study_1 = VariantStudy(id=1, name="study-1", tags=[test_tag_1])
    study_2 = VariantStudy(id=2, name="study-2", tags=[test_tag_2])
    study_3 = VariantStudy(id=3, name="study-3", tags=[test_tag_3])
    study_4 = VariantStudy(id=4, name="study-4", tags=[test_tag_2, test_tag_3])
    study_5 = RawStudy(id=5, name="study-5", tags=[test_tag_1])
    study_6 = RawStudy(id=6, name="study-6", tags=[test_tag_2])
    study_7 = RawStudy(id=7, name="study-7", tags=[test_tag_3])
    study_8 = RawStudy(id=8, name="study-8", tags=[test_tag_2, test_tag_3])

    db_session.add_all([study_1, study_2, study_3, study_4, study_5, study_6, study_7, study_8])
    db_session.commit()

    # use the db recorder to check that:
    # 1- retrieving all studies requires only 1 query
    # 2- accessing studies attributes does not require additional queries to db
    # 3- having an exact total of queries equals to 1
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(
            study_filter=StudyFilter(tags=tags, access_permissions=AccessPermissions(is_admin=True))
        )
        _ = [s.owner for s in all_studies]
        _ = [s.groups for s in all_studies]
        _ = [s.additional_data for s in all_studies]
        _ = [s.tags for s in all_studies]

    assert len(db_recorder.sql_statements) == 1, str(db_recorder)

    if expected_ids is not None:
        assert sorted(s.id for s in all_studies) == expected_ids

    # test pagination
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(
            study_filter=StudyFilter(tags=tags, access_permissions=AccessPermissions(is_admin=True)),
            pagination=StudyPagination(page_nb=1, page_size=2),
        )
        assert len(all_studies) == max(0, min(len(expected_ids) - 2, 2))
        assert sorted(s.id for s in all_studies) == expected_ids[2:4]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)


# fmt: off
@pytest.mark.parametrize(
    "user_id, study_groups, expected_ids",
    [
        (101, [], ["1", "2", "5", "6", "7", "8", "9", "10", "13", "14", "15", "16", "17", "18",
                   "21", "22", "23", "24", "25", "26", "29", "30", "31", "32", "34"]),
        (101, ["101"], ["1", "7", "8", "9", "17", "23", "24", "25"]),
        (101, ["102"], ["2", "5", "6", "7", "8", "9", "18", "21", "22", "23", "24", "25", "34"]),
        (101, ["103"], []),
        (101, ["101", "102"], ["1", "2", "5", "6", "7", "8", "9", "17", "18", "21", "22", "23", "24", "25", "34"]),
        (101, ["101", "103"], ["1", "7", "8", "9", "17", "23", "24", "25"]),
        (101, ["102", "103"], ["2", "5", "6", "7", "8", "9", "18", "21", "22", "23", "24", "25", "34"]),
        (101, ["101", "102", "103"], ["1", "2", "5", "6", "7", "8", "9", "17", "18", "21", "22",
                                      "23", "24", "25", "34"]),
        (102, [], ["1", "3", "4", "5", "7", "8", "9", "11", "13", "14", "15", "16", "17", "19",
                   "20", "21", "23", "24", "25", "27", "29", "30", "31", "32", "33"]),
        (102, ["101"], ["1", "3", "4", "7", "8", "9", "17", "19", "20", "23", "24", "25", "33"]),
        (102, ["102"], ["5", "7", "8", "9", "21", "23", "24", "25"]),
        (102, ["103"], []),
        (102, ["101", "102"], ["1", "3", "4", "5", "7", "8", "9", "17", "19", "20", "21", "23", "24", "25", "33"]),
        (102, ["101", "103"], ["1", "3", "4", "7", "8", "9", "17", "19", "20", "23", "24", "25", "33"]),
        (102, ["102", "103"], ["5", "7", "8", "9", "21", "23", "24", "25"]),
        (102, ["101", "102", "103"], ["1", "3", "4", "5", "7", "8", "9", "17", "19", "20", "21",
                                      "23", "24", "25", "33"]),
        (103, [], ["13", "14", "15", "16", "29", "30", "31", "32", "33", "34", "35", "36"]),
        (103, ["101"], ["33"]),
        (103, ["102"], ["34"]),
        (103, ["103"], []),
        (103, ["101", "102"], ["33", "34"]),
        (103, ["101", "103"], ["33"]),
        (103, ["102", "103"], ["34"]),
        (103, ["101", "102", "103"], ["33", "34"]),
        (None, [], []),
        (None, ["101"], []),
        (None, ["102"], []),
        (None, ["103"], []),
        (None, ["101", "102"], []),
        (None, ["101", "103"], []),
        (None, ["102", "103"], []),
        (None, ["101", "102", "103"], []),
    ],
)
# fmt: on
def test_get_all__non_admin_permissions_filter(
    db_session: Session,
    user_id: t.Optional[int],
    study_groups: t.Sequence[str],
    expected_ids: t.List[str],
) -> None:
    icache: Mock = Mock(spec=ICache)
    repository = StudyMetadataRepository(cache_service=icache, session=db_session)

    user_1 = User(id=101, name="user1")
    user_2 = User(id=102, name="user2")
    user_3 = User(id=103, name="user3")

    group_1 = Group(id="101", name="group1")
    group_2 = Group(id="102", name="group2")
    group_3 = Group(id="103", name="group3")

    user_groups_mapping = {101: [group_2.id], 102: [group_1.id], 103: []}

    # create variant studies for user_1 and user_2 that are part of some groups
    study_1 = VariantStudy(id=1, name="study-1", owner=user_1, groups=[group_1])
    study_2 = VariantStudy(id=2, name="study-2", owner=user_1, groups=[group_2])
    study_3 = VariantStudy(id=3, name="study-3", groups=[group_1])
    study_4 = VariantStudy(id=4, name="study-4", owner=user_2, groups=[group_1])
    study_5 = VariantStudy(id=5, name="study-5", owner=user_2, groups=[group_2])
    study_6 = VariantStudy(id=6, name="study-6", groups=[group_2])
    study_7 = VariantStudy(id=7, name="study-7", owner=user_1, groups=[group_1, group_2])
    study_8 = VariantStudy(id=8, name="study-8", owner=user_2, groups=[group_1, group_2])
    study_9 = VariantStudy(id=9, name="study-9", groups=[group_1, group_2])
    study_10 = VariantStudy(id=10, name="study-X10", owner=user_1)
    study_11 = VariantStudy(id=11, name="study-X11", owner=user_2)

    # create variant studies with neither owner nor groups
    study_12 = VariantStudy(id=12, name="study-X12")
    study_13 = VariantStudy(id=13, name="study-X13", public_mode=PublicMode.READ)
    study_14 = VariantStudy(id=14, name="study-X14", public_mode=PublicMode.EDIT)
    study_15 = VariantStudy(id=15, name="study-X15", public_mode=PublicMode.EXECUTE)
    study_16 = VariantStudy(id=16, name="study-X16", public_mode=PublicMode.FULL)

    # create raw studies for user_1 and user_2 that are part of some groups
    study_17 = RawStudy(id=17, name="study-X17", owner=user_1, groups=[group_1])
    study_18 = RawStudy(id=18, name="study-X18", owner=user_1, groups=[group_2])
    study_19 = RawStudy(id=19, name="study-X19", groups=[group_1])
    study_20 = RawStudy(id=20, name="study-X20", owner=user_2, groups=[group_1])
    study_21 = RawStudy(id=21, name="study-X21", owner=user_2, groups=[group_2])
    study_22 = RawStudy(id=22, name="study-X22", groups=[group_2])
    study_23 = RawStudy(id=23, name="study-X23", owner=user_1, groups=[group_1, group_2])
    study_24 = RawStudy(id=24, name="study-X24", owner=user_2, groups=[group_1, group_2])
    study_25 = RawStudy(id=25, name="study-X25", groups=[group_1, group_2])
    study_26 = RawStudy(id=26, name="study-X26", owner=user_1)
    study_27 = RawStudy(id=27, name="study-X27", owner=user_2)

    # create raw studies with neither owner nor groups
    study_28 = RawStudy(id=28, name="study-X28")
    study_29 = RawStudy(id=29, name="study-X29", public_mode=PublicMode.READ)
    study_30 = RawStudy(id=30, name="study-X30", public_mode=PublicMode.EDIT)
    study_31 = RawStudy(id=31, name="study-X31", public_mode=PublicMode.EXECUTE)
    study_32 = RawStudy(id=32, name="study-X32", public_mode=PublicMode.FULL)

    # create studies for user_3 that is not part of any group
    study_33 = VariantStudy(id=33, name="study-X33", owner=user_3, groups=[group_1])
    study_34 = RawStudy(id=34, name="study-X34", owner=user_3, groups=[group_2])
    study_35 = VariantStudy(id=35, name="study-X35", owner=user_3)
    study_36 = RawStudy(id=36, name="study-X36", owner=user_3)

    # create studies for group_3 that has no user
    study_37 = VariantStudy(id=37, name="study-X37", groups=[group_3])
    study_38 = RawStudy(id=38, name="study-X38", groups=[group_3])

    db_session.add_all([user_1, user_2, user_3, group_1, group_2, group_3])
    # fmt: off
    db_session.add_all(
        [
            study_1, study_2, study_3, study_4, study_5, study_6, study_7, study_8, study_9, study_10,
            study_11, study_12, study_13, study_14, study_15, study_16, study_17, study_18, study_19, study_20,
            study_21, study_22, study_23, study_24, study_25, study_26, study_27, study_28, study_29, study_30,
            study_31, study_32, study_33, study_34, study_35, study_36, study_37, study_38
            ]
    )
    # fmt: on
    db_session.commit()

    access_permissions = (
        AccessPermissions(user_id=user_id, user_groups=user_groups_mapping.get(user_id))
        if user_id
        else AccessPermissions()
    )
    study_filter = (
        StudyFilter(groups=study_groups, access_permissions=access_permissions)
        if study_groups
        else StudyFilter(access_permissions=access_permissions)
    )

    # use the db recorder to check that:
    # 1- retrieving all studies requires only 1 query
    # 2- accessing studies attributes does not require additional queries to db
    # 3- having an exact total of queries equals to 1
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(study_filter=study_filter)
        _ = [s.owner for s in all_studies]
        _ = [s.groups for s in all_studies]
        _ = [s.additional_data for s in all_studies]
        _ = [s.tags for s in all_studies]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)

    if expected_ids is not None:
        assert sorted((s.id for s in all_studies), key=int) == expected_ids

    # test pagination
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(study_filter=study_filter, pagination=StudyPagination(page_nb=1, page_size=2))
        assert len(all_studies) == max(0, min(len(expected_ids) - 2, 2))
        assert sorted((s.id for s in all_studies), key=int) == expected_ids[2:4]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)

# fmt: off
@pytest.mark.parametrize(
    "is_admin, study_groups, expected_ids",
    [
        (True, [], [str(e) for e in range(1, 39)]),
        (True, ["101"], ["1", "3", "4", "7", "8", "9", "17", "19", "20", "23", "24", "25", "33"]),
        (True, ["102"], ["2", "5", "6", "7", "8", "9", "18", "21", "22", "23", "24", "25", "34"]),
        (True, ["103"], ["37", "38"]),
        (True, ["101", "102"], ["1", "2", "3", "4", "5", "6", "7", "8", "9", "17", "18", "19",
                                "20", "21", "22", "23", "24", "25", "33", "34"]),
        (True, ["101", "103"], ["1", "3", "4", "7", "8", "9", "17", "19", "20", "23", "24", "25", "33", "37", "38"]),
        (True, ["101", "102", "103"], ["1", "2", "3", "4", "5", "6", "7", "8", "9", "17", "18",
                                       "19", "20", "21", "22", "23", "24", "25", "33", "34", "37", "38"]),
        (False, [], []),
        (False, ["101"], []),
        (False, ["102"], []),
        (False, ["103"], []),
        (False, ["101", "102"], []),
        (False, ["101", "103"], []),
        (False, ["101", "102", "103"], []),
    ],
)
# fmt: on
def test_get_all__admin_permissions_filter(
    db_session: Session,
    is_admin: bool,
    study_groups: t.Sequence[str],
    expected_ids: t.List[str],
) -> None:
    icache: Mock = Mock(spec=ICache)
    repository = StudyMetadataRepository(cache_service=icache, session=db_session)
    user_1 = User(id=101, name="user1")
    user_2 = User(id=102, name="user2")
    user_3 = User(id=103, name="user3")

    group_1 = Group(id=101, name="group1")
    group_2 = Group(id=102, name="group2")
    group_3 = Group(id=103, name="group3")

    # create variant studies for user_1 and user_2 that are part of some groups
    study_1 = VariantStudy(id=1, name="study-1", owner=user_1, groups=[group_1])
    study_2 = VariantStudy(id=2, name="study-2", owner=user_1, groups=[group_2])
    study_3 = VariantStudy(id=3, name="study-3", groups=[group_1])
    study_4 = VariantStudy(id=4, name="study-4", owner=user_2, groups=[group_1])
    study_5 = VariantStudy(id=5, name="study-5", owner=user_2, groups=[group_2])
    study_6 = VariantStudy(id=6, name="study-6", groups=[group_2])
    study_7 = VariantStudy(id=7, name="study-7", owner=user_1, groups=[group_1, group_2])
    study_8 = VariantStudy(id=8, name="study-8", owner=user_2, groups=[group_1, group_2])
    study_9 = VariantStudy(id=9, name="study-9", groups=[group_1, group_2])
    study_10 = VariantStudy(id=10, name="study-X10", owner=user_1)
    study_11 = VariantStudy(id=11, name="study-X11", owner=user_2)

    # create variant studies with neither owner nor groups
    study_12 = VariantStudy(id=12, name="study-X12")
    study_13 = VariantStudy(id=13, name="study-X13", public_mode=PublicMode.READ)
    study_14 = VariantStudy(id=14, name="study-X14", public_mode=PublicMode.EDIT)
    study_15 = VariantStudy(id=15, name="study-X15", public_mode=PublicMode.EXECUTE)
    study_16 = VariantStudy(id=16, name="study-X16", public_mode=PublicMode.FULL)

    # create raw studies for user_1 and user_2 that are part of some groups
    study_17 = RawStudy(id=17, name="study-X17", owner=user_1, groups=[group_1])
    study_18 = RawStudy(id=18, name="study-X18", owner=user_1, groups=[group_2])
    study_19 = RawStudy(id=19, name="study-X19", groups=[group_1])
    study_20 = RawStudy(id=20, name="study-X20", owner=user_2, groups=[group_1])
    study_21 = RawStudy(id=21, name="study-X21", owner=user_2, groups=[group_2])
    study_22 = RawStudy(id=22, name="study-X22", groups=[group_2])
    study_23 = RawStudy(id=23, name="study-X23", owner=user_1, groups=[group_1, group_2])
    study_24 = RawStudy(id=24, name="study-X24", owner=user_2, groups=[group_1, group_2])
    study_25 = RawStudy(id=25, name="study-X25", groups=[group_1, group_2])
    study_26 = RawStudy(id=26, name="study-X26", owner=user_1)
    study_27 = RawStudy(id=27, name="study-X27", owner=user_2)

    # create raw studies with neither owner nor groups
    study_28 = RawStudy(id=28, name="study-X28")
    study_29 = RawStudy(id=29, name="study-X29", public_mode=PublicMode.READ)
    study_30 = RawStudy(id=30, name="study-X30", public_mode=PublicMode.EDIT)
    study_31 = RawStudy(id=31, name="study-X31", public_mode=PublicMode.EXECUTE)
    study_32 = RawStudy(id=32, name="study-X32", public_mode=PublicMode.FULL)

    # create studies for user_3 that is not part of any group
    study_33 = VariantStudy(id=33, name="study-X33", owner=user_3, groups=[group_1])
    study_34 = RawStudy(id=34, name="study-X34", owner=user_3, groups=[group_2])
    study_35 = VariantStudy(id=35, name="study-X35", owner=user_3)
    study_36 = RawStudy(id=36, name="study-X36", owner=user_3)

    # create studies for group_3 that has no user
    study_37 = VariantStudy(id=37, name="study-X37", groups=[group_3])
    study_38 = RawStudy(id=38, name="study-X38", groups=[group_3])

    db_session.add_all([user_1, user_2, user_3, group_1, group_2, group_3])
    # fmt: off
    db_session.add_all(
        [
            study_1, study_2, study_3, study_4, study_5, study_6, study_7, study_8, study_9, study_10,
            study_11, study_12, study_13, study_14, study_15, study_16, study_17, study_18, study_19, study_20,
            study_21, study_22, study_23, study_24, study_25, study_26, study_27, study_28, study_29, study_30,
            study_31, study_32, study_33, study_34, study_35, study_36, study_37, study_38
            ]
    )
    # fmt: on
    db_session.commit()

    access_permissions = AccessPermissions(is_admin=is_admin)

    study_filter = (
        StudyFilter(groups=study_groups, access_permissions=access_permissions)
        if study_groups
        else StudyFilter(access_permissions=access_permissions)
    )
    # use the db recorder to check that:
    # 1- retrieving all studies requires only 1 query
    # 2- accessing studies attributes does not require additional queries to db
    # 3- having an exact total of queries equals to 1
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(study_filter=study_filter)
        _ = [s.owner for s in all_studies]
        _ = [s.groups for s in all_studies]
        _ = [s.additional_data for s in all_studies]
        _ = [s.tags for s in all_studies]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)

    if expected_ids is not None:
        assert sorted((s.id for s in all_studies), key=int) == expected_ids

    # test pagination
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(study_filter=study_filter, pagination=StudyPagination(page_nb=1, page_size=2))
        assert len(all_studies) == max(0, min(len(expected_ids) - 2, 2))
        assert sorted((s.id for s in all_studies), key=int) == expected_ids[2:4]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)


def test_update_tags(
    db_session: Session,
) -> None:
    icache: Mock = Mock(spec=ICache)
    repository = StudyMetadataRepository(cache_service=icache, session=db_session)

    study_id = 1
    study = RawStudy(id=study_id, name=f"study-{study_id}", tags=[])
    db_session.add(study)
    db_session.commit()

    # use the db recorder to check that:
    # 1- finding existing tags requires 1 query
    # 2- updating the study tags requires 4 queries (2 selects, 2 inserts)
    # 3- deleting orphan tags requires 1 query
    with DBStatementRecorder(db_session.bind) as db_recorder:
        repository.update_tags(study, ["Tag1", "Tag2"])
    assert len(db_recorder.sql_statements) == 6, str(db_recorder)

    # Check that when we change the tags to ["TAG1", "Tag3"],
    # "Tag1" is preserved, "Tag2" is deleted and "Tag3" is created
    # 1- finding existing tags requires 1 query
    # 2- updating the study tags requires 4 queries (2 selects, 2 inserts, 1 delete)
    # 3- deleting orphan tags requires 1 query
    with DBStatementRecorder(db_session.bind) as db_recorder:
        repository.update_tags(study, ["TAG1", "Tag3"])
    assert len(db_recorder.sql_statements) == 7, str(db_recorder)

    # Check that only "Tag1" and "Tag3" are present in the database
    tags = db_session.query(Tag).all()
    assert {tag.label for tag in tags} == {"Tag1", "Tag3"}


@pytest.mark.parametrize(
    "managed, study_ids, exists, expected_ids",
    [
        (None, [], False, ["5", "6"]),
        (None, [], True, ["1", "2", "3", "4", "7", "8"]),
        (None, [], None, ["1", "2", "3", "4", "5", "6", "7", "8"]),
        (None, ["1", "3", "5", "7"], False, ["5"]),
        (None, ["1", "3", "5", "7"], True, ["1", "3", "7"]),
        (None, ["1", "3", "5", "7"], None, ["1", "3", "5", "7"]),
        (True, [], False, ["5"]),
        (True, [], True, ["1", "2", "3", "4", "8"]),
        (True, [], None, ["1", "2", "3", "4", "5", "8"]),
        (True, ["1", "3", "5", "7"], False, ["5"]),
        (True, ["1", "3", "5", "7"], True, ["1", "3"]),
        (True, ["1", "3", "5", "7"], None, ["1", "3", "5"]),
        (True, ["2", "4", "6", "8"], True, ["2", "4", "8"]),
        (True, ["2", "4", "6", "8"], None, ["2", "4", "8"]),
        (False, [], False, ["6"]),
        (False, [], True, ["7"]),
        (False, [], None, ["6", "7"]),
        (False, ["1", "3", "5", "7"], False, []),
        (False, ["1", "3", "5", "7"], True, ["7"]),
        (False, ["1", "3", "5", "7"], None, ["7"]),
    ],
)
def test_count_studies__general_case(
    db_session: Session,
    managed: t.Union[bool, None],
    study_ids: t.Sequence[str],
    exists: t.Union[bool, None],
    expected_ids: t.List[str],
) -> None:
    test_workspace = "test-repository"
    icache: Mock = Mock(spec=ICache)
    repository = StudyMetadataRepository(cache_service=icache, session=db_session)

    study_1 = VariantStudy(id="1", name="study-1")
    study_2 = VariantStudy(id="2", name="study-2")
    study_3 = VariantStudy(id="3", name="study-3")
    study_4 = VariantStudy(id="4", name="study-4")
    study_5 = RawStudy(id="5", name="study-5", missing=datetime.datetime.now(), workspace=DEFAULT_WORKSPACE_NAME)
    study_6 = RawStudy(id="6", name="study-6", missing=datetime.datetime.now(), workspace=test_workspace)
    study_7 = RawStudy(id="7", name="study-7", missing=None, workspace=test_workspace)
    study_8 = RawStudy(id="8", name="study-8", missing=None, workspace=DEFAULT_WORKSPACE_NAME)

    db_session.add_all([study_1, study_2, study_3, study_4, study_5, study_6, study_7, study_8])
    db_session.commit()

    # use the db recorder to check that:
    # 1- retrieving all studies requires only 1 query
    # 2- accessing studies attributes does not require additional queries to db
    # 3- having an exact total of queries equals to 1
    with DBStatementRecorder(db_session.bind) as db_recorder:
        count = repository.count_studies(
            study_filter=StudyFilter(
                managed=managed,
                study_ids=study_ids,
                exists=exists,
                access_permissions=AccessPermissions(is_admin=True),
            )
        )
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)

    # test that the expected studies are returned
    if expected_ids is not None:
        assert count == len(expected_ids)
