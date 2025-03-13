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

import json
from datetime import datetime

from sqlalchemy.orm import Session 

from antarest.core.cache.business.local_chache import LocalCache
from antarest.core.model import PublicMode
from antarest.login.model import Group, User
from antarest.study.model import DEFAULT_WORKSPACE_NAME, RawStudy, Study, StudyAdditionalData, StudyContentStatus
from antarest.study.repository import AccessPermissions, StudyFilter, StudyMetadataRepository
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

    assert len(repo.get_all(study_filter=StudyFilter(access_permissions=AccessPermissions(is_admin=True)))) == 4
    assert len(repo.get_all_raw(exists=True)) == 1
    assert len(repo.get_all_raw(exists=False)) == 1
    assert len(repo.get_all_raw()) == 2

    repo.delete(a_id)
    assert repo.get(a_id) is None


def test_study__additional_data(db_session: Session) -> None:
    repo = StudyMetadataRepository(LocalCache(), session=db_session)

    user = User(id=0, name="admin")
    group = Group(id="my-group", name="group")

    patch = {"foo": "bar"}
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
        additional_data=StudyAdditionalData(author="John Smith", horizon="2024-2050", patch=json.dumps(patch)),
    )

    repo.save(a)
    a_id = a.id

    # Check that the additional data is correctly saved
    additional_data = repo.get_additional_data(a_id)
    assert additional_data.author == "John Smith"
    assert additional_data.horizon == "2024-2050"
    assert json.loads(additional_data.patch) == patch

    # Check that the additional data is correctly updated
    new_patch = {"foo": "baz"}
    a.additional_data.patch = json.dumps(new_patch)
    repo.save(a)
    additional_data = repo.get_additional_data(a_id)
    assert json.loads(additional_data.patch) == new_patch

    # Check that the additional data is correctly deleted when the study is deleted
    repo.delete(a_id)
    assert repo.get_additional_data(a_id) is None


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
