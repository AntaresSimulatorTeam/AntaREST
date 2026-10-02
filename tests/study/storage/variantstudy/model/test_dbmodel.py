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

import datetime
import json
import uuid
from pathlib import Path

import pytest
from antares.study.version import StudyVersion
from sqlalchemy.orm import Session

from antarest.core.model import PublicMode
from antarest.core.roles import RoleType
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.sql_utils import upsert_one
from antarest.core.utils.utils import current_time
from antarest.login.model import Group, Role, User
from antarest.study.model import StorageMode
from antarest.study.storage.variantstudy.model.dbmodel import (
    CommandBlock,
    CommandsListVersion,
    VariantStudy,
    VariantStudySnapshot,
)
from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService
from tests.helpers import create_raw_study, create_variant_study, with_db_context


@pytest.fixture(name="user_id")
def fixture_user_id(db_session: Session) -> int:
    with db_session:
        user_id = 0o007
        james = User(id=user_id, name="James Bond")
        role = Role(
            type=RoleType.WRITER,
            identity=james,
            group=Group(id="writers"),
        )
        db_session.add(role)
        db_session.commit()
    return user_id


@pytest.fixture(name="raw_study_id")
def fixture_raw_study_id(tmp_path: Path, db_session: Session, user_id: int) -> str:
    with db_session:
        root_study_id = str(uuid.uuid4())
        root_study = create_raw_study(
            id=root_study_id,
            workspace="default",
            path=str(tmp_path.joinpath("root_study")),
            version="860",
            created_at=datetime.datetime.now(datetime.UTC).replace(tzinfo=None),
            updated_at=datetime.datetime.now(datetime.UTC).replace(tzinfo=None),
            author="john.doe",
            owner_id=user_id,
        )
        db_session.add(root_study)
        db_session.commit()
    return root_study_id


@pytest.fixture(name="variant_study_id")
def fixture_variant_study_id(tmp_path: Path, db_session: Session, raw_study_id: str, user_id: int) -> str:
    with db_session:
        variant_study_id = str(uuid.uuid4())
        now = current_time()
        variant = create_variant_study(
            id=variant_study_id,
            name="Variant Study",
            version="860",
            author="John DOE",
            parent_id=raw_study_id,
            created_at=now - datetime.timedelta(days=1),
            updated_at=now,
            last_access=now,
            path=str(tmp_path.joinpath("variant_study")),
            owner_id=user_id,
        )
        db_session.add(variant)
        db_session.commit()
    return variant_study_id


class TestVariantStudySnapshot:
    def test_init__without_command(self, db_session: Session, variant_study_id: str) -> None:
        """
        Check the creation of an instance of VariantStudySnapshot
        """
        with db_session:
            snap = VariantStudySnapshot(id=variant_study_id, version=13)
            db_session.add(snap)
            db_session.commit()

        obj: VariantStudySnapshot = (
            db_session.query(VariantStudySnapshot).filter(VariantStudySnapshot.id == variant_study_id).one()
        )

        # check Study representation
        assert str(obj).startswith(f"[Snapshot] id={variant_study_id}")

        # check Study fields
        assert obj.id == variant_study_id
        assert obj.version == 13
        assert obj.last_executed_command is None

    def test_init__with_command(self, db_session: Session, variant_study_id: str) -> None:
        """
        Check the creation of an instance of VariantStudySnapshot
        """
        command_id = str(uuid.uuid4())

        with db_session:
            snap = VariantStudySnapshot(id=variant_study_id, version=2, last_executed_command=command_id)
            db_session.add(snap)
            db_session.commit()

        obj: VariantStudySnapshot = (
            db_session.query(VariantStudySnapshot).filter(VariantStudySnapshot.id == variant_study_id).one()
        )
        assert obj.id == variant_study_id
        assert obj.version == 2
        assert obj.last_executed_command == command_id


class TestCommandBlock:
    def test_init(self, db_session: Session, variant_study_id: str, user_id: int) -> None:
        """
        Check the creation of an instance of CommandBlock
        """
        command_id = str(uuid.uuid4())
        index = 7
        command = "dummy command"
        version = 42
        args = '{"foo": "bar"}'
        updated_at = current_time()

        with db_session:
            block = CommandBlock(
                id=command_id,
                study_id=variant_study_id,
                index=index,
                command=command,
                version=version,
                args=args,
                study_version="860",
                updated_at=updated_at,
                user_id=user_id,
            )
            db_session.add(block)
            db_session.commit()

        obj: CommandBlock = db_session.query(CommandBlock).filter(CommandBlock.id == command_id).one()

        # check CommandBlock representation
        assert str(obj).startswith(f"CommandBlock(id={command_id!r}")

        # check CommandBlock fields
        assert obj.id == command_id
        assert obj.study_id == variant_study_id
        assert obj.index == index
        assert obj.command == command
        assert obj.version == version
        assert obj.args == args

        # check CommandBlock.to_dto()
        dto = obj.to_dto()
        # note: it is easier to compare the dict representation of the DTO
        assert dto.model_dump() == {
            "id": command_id,
            "action": command,
            "args": json.loads(args),
            "version": 42,
            "study_version": StudyVersion.parse("860"),
            "updated_at": updated_at.replace(tzinfo=None),
            "user_id": user_id,
        }


class TestVariantStudy:
    def test_init__without_snapshot(self, db_session: Session, raw_study_id: str, user_id: int) -> None:
        """
        Check the creation of an instance of variant study without snapshot
        """
        now = current_time()
        variant_study_id = str(uuid.uuid4())
        variant_study_path = "path/to/variant"

        with db_session:
            variant = create_variant_study(
                id=variant_study_id,
                name="Variant Study",
                version="860",
                author="John DOE",
                parent_id=raw_study_id,
                created_at=now - datetime.timedelta(days=1),
                updated_at=now,
                last_access=now,
                path=variant_study_path,
                owner_id=user_id,
            )
            db_session.add(variant)
            db_session.commit()

        obj: VariantStudy = db_session.query(VariantStudy).filter(VariantStudy.id == variant_study_id).one()

        # check Study representation
        assert str(obj).startswith(f"[VariantStudy] id={variant_study_id}")

        # check Study fields
        assert obj.id == variant_study_id
        assert obj.name == "Variant Study"
        assert obj.type == "variantstudy"
        assert obj.version == "860"
        assert obj.author == "John DOE"
        assert obj.created_at == (now - datetime.timedelta(days=1)).replace(tzinfo=None)
        assert obj.updated_at == now.replace(tzinfo=None)
        assert obj.last_access == now.replace(tzinfo=None)
        assert obj.path == variant_study_path
        assert obj.folder is None
        assert obj.parent_id == raw_study_id
        assert obj.public_mode == PublicMode.NONE
        assert obj.owner_id == user_id
        assert obj.archived is False
        assert obj.groups == []

        # check Variant-specific fields
        assert obj.generation_task is None
        assert obj.snapshot is None
        assert obj.commands == []


def _set_up(session: Session, parent_id: int, user_id: int) -> str:
    with session:
        # Given a variant study (referencing the raw study)
        # with optionally a snapshot and a snapshot directory
        variant_id = str(uuid.uuid4())
        variant = create_variant_study(
            id=variant_id,
            name="Study 3.0",
            author="Sandrine",
            parent_id=parent_id,
            path="",
            owner_id=user_id,
            storage_mode=StorageMode.FILESYSTEM,
            commands_version=CommandsListVersion(version=0, variant_id=variant_id),
        )

        session.add(variant)
        session.commit()

        return variant_id


@with_db_context
def test_is_snapshot_up_to_date(variant_study_service: VariantStudyService, raw_study_id: int, user_id: int) -> None:
    """
    Check the `is_snapshot_up_to_date()` method
    """
    session = db.session
    variant_id = _set_up(session, raw_study_id, user_id)

    # 1st case, no snapshot in DB -> Not up to date
    variant = session.get(VariantStudy, variant_id)
    assert variant_study_service.repository.is_snapshot_up_to_date(variant_id) is False

    # 2nd case: Add the snapshot in DB with a version 0 which matches the command blocks version -> Up to date
    variant.snapshot = VariantStudySnapshot(id=variant_id, version=0, last_executed_command=None)
    session.add(variant)
    session.commit()

    variant = session.get(VariantStudy, variant_id)
    assert variant_study_service.repository.is_snapshot_up_to_date(variant_id) is True

    # 3rd case: Changes the version in `commands_list_version` table -> Not up to date
    upsert_one(session, CommandsListVersion.__table__, {"variant_id": variant_id, "version": 1})
    session.commit()

    variant = session.get(VariantStudy, variant_id)
    session.refresh(variant)
    assert variant_study_service.repository.is_snapshot_up_to_date(variant_id) is False

    # 4th case: Adapt the version in the study snapshot to match the commands one -> Up to date
    variant.snapshot.version = 1
    session.add(variant)
    session.commit()

    assert variant_study_service.repository.is_snapshot_up_to_date(variant_id) is True
