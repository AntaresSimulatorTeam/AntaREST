# Copyright (c) 2026, RTE (https://www.rte-france.com)
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


from helpers import create_raw_study, create_study, create_variant_study
from sqlalchemy.orm import Session

from antarest.core.cache.business.local_chache import LocalCache
from antarest.core.model import PublicMode
from antarest.core.utils.utils import current_time
from antarest.login.model import Group, User
from antarest.study.model import DEFAULT_WORKSPACE_NAME, RawStudy, StudyContentStatus
from antarest.study.repository import AccessPermissions, StudyFilter, StudyMetadataRepository


def test_lifecycle(db_session: Session) -> None:
    repo = StudyMetadataRepository(LocalCache(), session=db_session)

    user = User(id=1, name="admin")
    group = Group(id="my-group", name="group")
    now = current_time()
    a = create_study(
        name="a",
        version="820",
        author="John Smith",
        created_at=now,
        updated_at=now,
        public_mode=PublicMode.FULL,
        owner=user,
        groups=[group],
    )
    b = create_raw_study(
        name="b",
        version="830",
        author="Morpheus",
        created_at=now,
        updated_at=now,
        public_mode=PublicMode.FULL,
        owner=user,
        groups=[group],
    )
    c = create_raw_study(
        name="c",
        version="830",
        author="Trinity",
        created_at=now,
        updated_at=now,
        public_mode=PublicMode.FULL,
        owner=user,
        groups=[group],
        missing=now,
    )
    d = create_variant_study(
        name="d",
        version="830",
        author="Mr. Anderson",
        created_at=now,
        updated_at=now,
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

    assert len(repo.get_all(study_filter=StudyFilter(access_permissions=AccessPermissions(is_admin=True)))) == 4
    assert len(repo.get_all_raw(exists=True)) == 1
    assert len(repo.get_all_raw(exists=False)) == 1
    assert len(repo.get_all_raw()) == 2

    repo.delete(a_id)
    assert repo.get(a_id) is None


def test_study_inheritance(db_session: Session) -> None:
    repo = StudyMetadataRepository(LocalCache(), session=db_session)

    user = User(id=0, name="admin")
    group = Group(id="my-group", name="group")
    now = current_time()
    a = create_raw_study(
        name="a",
        version="820",
        author="John Smith",
        created_at=now,
        updated_at=now,
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
