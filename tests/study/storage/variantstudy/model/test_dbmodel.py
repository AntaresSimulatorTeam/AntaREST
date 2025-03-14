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
import json
import typing as t
import uuid
from pathlib import Path

import pytest
from antares.study.version import StudyVersion
from sqlalchemy.orm import Session

from antarest.core.model import PublicMode
from antarest.core.roles import RoleType
from antarest.login.model import Group, Role, User
from antarest.study.model import RawStudy, StudyAdditionalData
from antarest.study.storage.variantstudy.model.dbmodel import CommandBlock, VariantStudy, VariantStudySnapshot


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
        root_study = RawStudy(
            id=root_study_id,
            workspace="default",
            path=str(tmp_path.joinpath("root_study")),
            version="860",
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow(),
            additional_data=StudyAdditionalData(author="john.doe"),
            owner_id=user_id,
        )
        db_session.add(root_study)
        db_session.commit()
    return root_study_id


@pytest.fixture(name="variant_study_id")
def fixture_variant_study_id(tmp_path: Path, db_session: Session, raw_study_id: str, user_id: int) -> str:
    with db_session:
        variant_study_id = str(uuid.uuid4())
        variant = VariantStudy(
            id=variant_study_id,
            name="Variant Study",
            version="860",
            author="John DOE",
            parent_id=raw_study_id,
            created_at=datetime.datetime.utcnow() - datetime.timedelta(days=1),
            updated_at=datetime.datetime.utcnow(),
            last_access=datetime.datetime.utcnow(),
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
        now = datetime.datetime.utcnow()

        with db_session:
            snap = VariantStudySnapshot(id=variant_study_id, created_at=now)
            db_session.add(snap)
            db_session.commit()

        obj: VariantStudySnapshot = (
            db_session.query(VariantStudySnapshot).filter(VariantStudySnapshot.id == variant_study_id).one()
        )

        # check Study representation
        assert str(obj).startswith(f"[Snapshot] id={variant_study_id}")

        # check Study fields
        assert obj.id == variant_study_id
        assert obj.created_at == now
        assert obj.last_executed_command is None

    def test_init__with_command(self, db_session: Session, variant_study_id: str) -> None:
        """
        Check the creation of an instance of VariantStudySnapshot
        """
        now = datetime.datetime.utcnow()
        command_id = str(uuid.uuid4())

        with db_session:
            snap = VariantStudySnapshot(id=variant_study_id, created_at=now, last_executed_command=command_id)
            db_session.add(snap)
            db_session.commit()

        obj: VariantStudySnapshot = (
            db_session.query(VariantStudySnapshot).filter(VariantStudySnapshot.id == variant_study_id).one()
        )
        assert obj.id == variant_study_id
        assert obj.created_at == now
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
        updated_at = datetime.datetime.utcnow()

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
            "updated_at": updated_at,
            "user_id": user_id,
        }


class TestVariantStudy:
    def test_init__without_snapshot(self, db_session: Session, raw_study_id: str, user_id: int) -> None:
        """
        Check the creation of an instance of variant study without snapshot
        """
        now = datetime.datetime.utcnow()
        variant_study_id = str(uuid.uuid4())
        variant_study_path = "path/to/variant"

        with db_session:
            variant = VariantStudy(
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
        assert obj.created_at == now - datetime.timedelta(days=1)
        assert obj.updated_at == now
        assert obj.last_access == now
        assert obj.path == variant_study_path
        assert obj.folder is None
        assert obj.parent_id == raw_study_id
        assert obj.public_mode == PublicMode.NONE
        assert obj.owner_id == user_id
        assert obj.archived is False
        assert obj.groups == []
        assert obj.additional_data is None

        # check Variant-specific fields
        assert obj.generation_task is None
        assert obj.snapshot is None
        assert obj.commands == []

        # check Variant-specific properties
        assert obj.snapshot_dir == Path(variant_study_path).joinpath("snapshot")
        assert obj.is_snapshot_up_to_date() is False

    @pytest.mark.parametrize(
        "created_at, updated_at, study_antares_file, expected",
        [
            pytest.param(
                datetime.datetime(2023, 11, 9),
                datetime.datetime(2023, 11, 8),
                "study.antares",
                True,
                id="with-recent-snapshot",
            ),
            pytest.param(
                datetime.datetime(2023, 11, 7),
                datetime.datetime(2023, 11, 8),
                "study.antares",
                False,
                id="with-old-snapshot",
            ),
            pytest.param(
                datetime.datetime(2023, 11, 9),
                datetime.datetime(2023, 11, 8),
                "dirty.antares",
                False,
                id="with-dirty-snapshot",
            ),
            pytest.param(
                None,
                datetime.datetime(2023, 11, 8),
                "study.antares",
                False,
                id="without-snapshot",
            ),
        ],
    )
    def test_is_snapshot_recent(
        self,
        db_session: Session,
        tmp_path: Path,
        raw_study_id: int,
        user_id: int,
        created_at: t.Optional[datetime.datetime],
        updated_at: datetime.datetime,
        study_antares_file: str,
        expected: bool,
    ) -> None:
        """
        Check the snapshot_uptodate() method
        """
        with db_session:
            # Given a variant study (referencing the raw study)
            # with optionally a snapshot and a snapshot directory
            variant_id = str(uuid.uuid4())
            variant = VariantStudy(
                id=variant_id,
                name="Study 3.0",
                author="Sandrine",
                parent_id=raw_study_id,
                updated_at=updated_at,
                path=str(tmp_path.joinpath("variant")),
                owner_id=user_id,
            )

            # If the snapshot creation date is given, we create a snapshot
            # and a snapshot directory.
            if created_at:
                variant.snapshot = VariantStudySnapshot(created_at=created_at)
                variant.snapshot_dir.mkdir(parents=True, exist_ok=True)

            # If the "study.antares" file is given, we create it in the snapshot directory.
            if study_antares_file:
                variant.snapshot_dir.mkdir(parents=True, exist_ok=True)
                (variant.snapshot_dir / study_antares_file).touch()

            db_session.add(variant)
            db_session.commit()

        # Check the snapshot_uptodate() method
        obj: VariantStudy = db_session.query(VariantStudy).filter(VariantStudy.id == variant_id).one()
        assert obj.is_snapshot_up_to_date() == expected
