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
import logging
import re
import typing as t
import uuid
from pathlib import Path
from unittest.mock import Mock

import numpy as np
import pytest
from antares.study.version import StudyVersion

from antarest.core.cache.business.local_chache import LocalCache
from antarest.core.exceptions import VariantGenerationError
from antarest.core.interfaces.cache import CacheConstants, update_cache
from antarest.core.jwt import JWTGroup, JWTUser
from antarest.core.roles import RoleType
from antarest.core.serde.ini_reader import IniReader
from antarest.core.tasks.service import ITaskNotifier
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.login.model import Group, Role, User
from antarest.login.utils import current_user_context
from antarest.study.model import StudyAdditionalData
from antarest.study.service import VariantStudyInterface
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfigDTO
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.variantstudy.model.dbmodel import CommandBlock, VariantStudy, VariantStudySnapshot
from antarest.study.storage.variantstudy.model.model import CommandDTO
from antarest.study.storage.variantstudy.snapshot_generator import SnapshotGenerator, search_ref_study
from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService
from tests.db_statement_recorder import DBStatementRecorder
from tests.helpers import (
    AnyUUID,
    create_raw_study,
    create_study,
    create_variant_study,
    with_admin_user,
    with_db_context,
)

logger = logging.getLogger(__name__)


def _create_variant(
    tmp_path: Path,
    variant_name: str,
    parent_id: str,
    updated_at: datetime.datetime,
    snapshot_created_at: t.Optional[datetime.datetime],
) -> VariantStudy:
    """
    Create a variant study with a snapshot (if snapshot_created_at is provided).
    """
    variant_dir = tmp_path.joinpath(f"some_place/{variant_name}")
    variant_dir.mkdir(parents=True, exist_ok=True)
    variant = create_variant_study(
        id=str(uuid.uuid4()),
        name=variant_name,
        updated_at=updated_at,
        parent_id=parent_id,
        path=str(variant_dir),
    )

    if snapshot_created_at:
        snapshot_dir = variant_dir.joinpath("snapshot")
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        (snapshot_dir / "study.antares").touch()
        variant.snapshot = VariantStudySnapshot(
            id=variant.id,
            created_at=snapshot_created_at,
            last_executed_command=None,
        )

    return variant


class TestSearchRefStudy:
    """
    Test the `search_ref_study` method of the `SnapshotGenerator` class.

    We need to test several cases:

    Cases where we expect to have the root study and a list of `CommandBlock`
    for all variants in the order of the list.

    - The edge case where the list of studies is empty.
      Note: This case is unlikely, but the function should be able to handle it.

    - The case where the list of studies contains variants with or without snapshots,
      but a search is requested from scratch.

    - The case where the list of studies contains variants with obsolete snapshots, meaning that:
      - either there is no snapshot,
      - or the snapshot's creation date is earlier than the variant's last modification date.
      Note: The situation where the "snapshot/study.antares" file does not exist is not considered.

    Cases where we expect to have a different reference study than the root study
    and corresponding to a variant with an up-to-date snapshot.

    - The case where the list of studies contains two variants with up-to-date snapshots and
      where the first is older than the second, and a third variant without snapshot.
      We expect to have a reference study corresponding to the second variant
      and a list of commands for the second variant.

    - The case where the list of studies contains two variants with up-to-date snapshots and
      where the first is more recent than the second, and a third variant without snapshot.
      We expect to have a reference study corresponding to the first variant
      and a list of commands for both variants in order.

    - The case where the list of studies contains a variant with an up-to-date snapshot and
      corresponds to the generation of all commands for the variant.
      We expect to have an empty list of commands because the snapshot is already completely up-to-date.

    - The case where the list of studies contains a variant with an up-to-date snapshot and
      corresponds to a partial generation of commands for the variant.
      We expect to have a list of commands corresponding to the remaining commands.
    """

    def test_search_ref_study__empty_descendants(self) -> None:
        """
        Edge case where the list of studies is empty.
        We expect to have the root study and a list of `CommandBlock` for all variants
        in the order of the list.

        Note: This case is unlikely, but the function should be able to handle it.

        Given an empty list of descendants,
        When calling search_ref_study,
        Then the root study is returned as reference study,
        and an empty list of commands is returned.
        """
        root_study = create_study(id=str(uuid.uuid4()), name="root")
        references: t.Sequence[VariantStudy] = []
        search_result = search_ref_study(root_study, references)
        assert search_result.ref_study == root_study
        assert search_result.cmd_blocks == []
        assert search_result.force_regenerate is True

    def test_search_ref_study__from_scratch(self, tmp_path: Path) -> None:
        """
        Case where the list of studies contains variants with or without snapshots,
        but a search is requested from scratch.
        We expect to have the root study and a list of `CommandBlock` for all variants
        in the order of the list.

        Given a list of descendants with some variants with snapshots,
        When calling search_ref_study with the flag from_scratch=True,
        Then the root study is returned as reference study,
        and all commands of all variants are returned.
        """
        root_study = create_study(id=str(uuid.uuid4()), name="root")

        # Prepare some variants with snapshots
        variant1 = _create_variant(
            tmp_path,
            "variant1",
            root_study.id,
            datetime.datetime(year=2023, month=1, day=1),
            snapshot_created_at=datetime.datetime(year=2023, month=1, day=1),
        )
        variant2 = _create_variant(
            tmp_path,
            "variant2",
            variant1.id,
            datetime.datetime(year=2023, month=1, day=2),
            snapshot_created_at=datetime.datetime(year=2023, month=1, day=2),
        )
        variant3 = _create_variant(
            tmp_path,
            "variant3",
            variant2.id,
            datetime.datetime(year=2023, month=1, day=1),
            None,
        )

        # Add some variant commands
        variant1.commands = [
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant1.id,
                index=0,
                command="create_area",
                version=1,
                args='{"area_name": "DE"}',
            ),
        ]
        variant1.snapshot.last_executed_command = variant1.commands[0].id
        variant2.commands = [
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant2.id,
                index=0,
                command="create_thermal_cluster",
                version=1,
                args='{"area_name": "DE", "cluster_name": "DE", "cluster_type": "thermal"}',
            ),
        ]
        variant2.snapshot.last_executed_command = variant2.commands[0].id
        variant3.commands = [
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant3.id,
                index=0,
                command="update_thermal_clusters",
                version=1,
                args='{"cluster_properties": {"DE": {"DE": {"enabled": False}}}}',
            ),
        ]

        # Check the variants
        references = [variant1, variant2, variant3]
        search_result = search_ref_study(root_study, references, from_scratch=True)
        assert search_result.ref_study == root_study
        assert search_result.cmd_blocks == [c for v in [variant1, variant2, variant3] for c in v.commands]
        assert search_result.force_regenerate is True

    def test_search_ref_study__obsolete_snapshots(self, tmp_path: Path) -> None:
        """
        Case where the list of studies contains variants with obsolete snapshots, meaning that:
          - either there is no snapshot,
          - or the snapshot's creation date is earlier than the variant's last modification date.
          Note: The situation where the "snapshot/study.antares" file does not exist is not considered.
        The third variant has no snapshot, and must be generated from scratch.
        We expect to have a reference study corresponding to the root study
        and the list of commands of all variants in order.
        """
        root_study = create_study(id=str(uuid.uuid4()), name="root")

        # Prepare some variants with snapshots:
        # Variant 1 has no snapshot.
        variant1 = _create_variant(
            tmp_path,
            "variant1",
            root_study.id,
            datetime.datetime(year=2023, month=1, day=1),
            snapshot_created_at=None,
        )
        # Variant 2 has an obsolete snapshot.
        variant2 = _create_variant(
            tmp_path,
            "variant2",
            variant1.id,
            datetime.datetime(year=2023, month=1, day=2),
            snapshot_created_at=datetime.datetime(year=2023, month=1, day=1),
        )
        # Variant 3 has no snapshot.
        variant3 = _create_variant(
            tmp_path,
            "variant3",
            variant2.id,
            datetime.datetime(year=2023, month=1, day=3),
            snapshot_created_at=None,
        )

        # Add some variant commands
        variant1.commands = [
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant1.id,
                index=0,
                command="create_area",
                version=1,
                args='{"area_name": "DE"}',
            ),
        ]
        variant2.commands = [
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant2.id,
                index=0,
                command="create_thermal_cluster",
                version=1,
                args='{"area_name": "DE", "cluster_name": "DE", "cluster_type": "thermal"}',
            ),
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant2.id,
                index=1,
                command="create_thermal_cluster",
                version=1,
                args='{"area_name": "IT", "cluster_name": "IT", "cluster_type": "gas"}',
            ),
        ]
        variant2.snapshot.last_executed_command = variant2.commands[0].id
        variant3.commands = [
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant2.id,
                index=0,
                command="create_thermal_cluster",
                version=1,
                args='{"area_name": "BE", "cluster_name": "BE", "cluster_type": "oil"}',
            ),
        ]

        # Check the variants
        references = [variant1, variant2, variant3]
        search_result = search_ref_study(root_study, references)
        assert search_result.ref_study == root_study
        assert search_result.cmd_blocks == [c for v in [variant1, variant2, variant3] for c in v.commands]
        assert search_result.force_regenerate is True

    def test_search_ref_study__old_recent_snapshot(self, tmp_path: Path) -> None:
        """
        Case where the list of studies contains a variant with up-to-date snapshots and
        where the first is older than the second.
        The third variant has no snapshot, and must be generated from scratch.
        We expect to have a reference study corresponding to the second variant
        and the list of commands of the third variant.
        """
        root_study = create_study(id=str(uuid.uuid4()), name="root")

        # Prepare some variants with snapshots:
        # Variant 1 has an up-to-date snapshot.
        variant1 = _create_variant(
            tmp_path,
            "variant1",
            root_study.id,
            datetime.datetime(year=2023, month=1, day=1),
            snapshot_created_at=datetime.datetime(year=2023, month=1, day=1),
        )
        # Variant 2 has an up-to-date snapshot, but is more recent than variant 1.
        variant2 = _create_variant(
            tmp_path,
            "variant2",
            variant1.id,
            datetime.datetime(year=2023, month=1, day=2),
            snapshot_created_at=datetime.datetime(year=2023, month=1, day=3),
        )
        # Variant 3 has no snapshot.
        variant3 = _create_variant(
            tmp_path,
            "variant3",
            variant2.id,
            datetime.datetime(year=2023, month=1, day=3),
            snapshot_created_at=None,
        )

        # Add some variant commands
        variant1.commands = [
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant1.id,
                index=0,
                command="create_area",
                version=1,
                args='{"area_name": "DE"}',
            ),
        ]
        variant1.snapshot.last_executed_command = variant1.commands[0].id
        variant2.commands = [
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant2.id,
                index=0,
                command="create_thermal_cluster",
                version=1,
                args='{"area_name": "DE", "cluster_name": "DE", "cluster_type": "thermal"}',
            ),
        ]
        variant2.snapshot.last_executed_command = variant2.commands[0].id
        variant3.commands = [
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant2.id,
                index=0,
                command="create_thermal_cluster",
                version=1,
                args='{"area_name": "BE", "cluster_name": "BE", "cluster_type": "oil"}',
            ),
        ]

        # Check the variants
        references = [variant1, variant2, variant3]
        search_result = search_ref_study(root_study, references)
        assert search_result.ref_study == variant2
        assert search_result.cmd_blocks == variant3.commands
        assert search_result.force_regenerate is True

    def test_search_ref_study__recent_old_snapshot(self, tmp_path: Path) -> None:
        """
        Case where the list of studies contains a variant with up-to-date snapshots and
        where the second is older than the first.
        The third variant has no snapshot, and must be generated from scratch.
        We expect to have a reference study corresponding to the first variant
        and the list of commands of the second and third variants.
        """
        root_study = create_study(id=str(uuid.uuid4()), name="root")

        # Prepare some variants with snapshots:
        # Variant 1 has an up-to-date snapshot, but is more recent than variant 2.
        variant1 = _create_variant(
            tmp_path,
            "variant1",
            root_study.id,
            datetime.datetime(year=2023, month=1, day=1),
            snapshot_created_at=datetime.datetime(year=2023, month=1, day=3),
        )
        # Variant 2 has an up-to-date snapshot, but is older that variant 1.
        variant2 = _create_variant(
            tmp_path,
            "variant2",
            variant1.id,
            datetime.datetime(year=2023, month=1, day=2),
            snapshot_created_at=datetime.datetime(year=2023, month=1, day=2),
        )
        # Variant 3 has no snapshot.
        variant3 = _create_variant(
            tmp_path,
            "variant3",
            variant2.id,
            datetime.datetime(year=2023, month=1, day=3),
            snapshot_created_at=None,
        )

        # Add some variant commands
        variant1.commands = [
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant1.id,
                index=0,
                command="create_area",
                version=1,
                args='{"area_name": "DE"}',
            ),
        ]
        variant1.snapshot.last_executed_command = variant1.commands[0].id
        variant2.commands = [
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant2.id,
                index=0,
                command="create_thermal_cluster",
                version=1,
                args='{"area_name": "DE", "cluster_name": "DE", "cluster_type": "thermal"}',
            ),
        ]
        variant2.snapshot.last_executed_command = variant2.commands[0].id
        variant3.commands = [
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant2.id,
                index=0,
                command="create_thermal_cluster",
                version=1,
                args='{"area_name": "BE", "cluster_name": "BE", "cluster_type": "oil"}',
            ),
        ]

        # Check the variants
        references = [variant1, variant2, variant3]
        search_result = search_ref_study(root_study, references)
        assert search_result.ref_study == variant1
        assert search_result.cmd_blocks == [c for v in [variant2, variant3] for c in v.commands]
        assert search_result.force_regenerate is True

    def test_search_ref_study__one_variant_completely_uptodate(self, tmp_path: Path) -> None:
        """
        Case where the list of studies contains a variant with an up-to-date snapshot and
        corresponds to the generation of all commands for the variant (completely up-to-date)
        We expect to have an empty list of commands because the snapshot is already completely up-to-date.

        Given a list of descendants with some variants with up-to-date snapshots,
        When calling search_ref_study with the flag from_scratch=False,
        Then the variant is returned as reference study, and no commands are returned.
        """
        root_study = create_study(id=str(uuid.uuid4()), name="root")

        # Prepare some variants with snapshots:
        variant1 = _create_variant(
            tmp_path,
            "variant1",
            root_study.id,
            datetime.datetime(year=2023, month=1, day=1),
            snapshot_created_at=datetime.datetime(year=2023, month=1, day=2),
        )

        # Add some variant commands
        variant1.commands = [
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant1.id,
                index=0,
                command="create_area",
                version=1,
                args='{"area_name": "DE"}',
            ),
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant1.id,
                index=1,
                command="create_thermal_cluster",
                version=1,
                args='{"area_name": "DE", "cluster_name": "DE", "cluster_type": "thermal"}',
            ),
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant1.id,
                index=2,
                command="update_thermal_clusters",
                version=1,
                args='{"cluster_properties": {"DE": {"DE": {"enabled": False}}}}',
            ),
        ]

        # The last executed command is the last item of the commands list.
        variant1.snapshot.last_executed_command = variant1.commands[-1].id

        # Check the variants
        references = [variant1]
        search_result = search_ref_study(root_study, references)
        assert search_result.ref_study == variant1
        assert search_result.cmd_blocks == []
        assert search_result.force_regenerate is False

    def test_search_ref_study__one_variant_partially_uptodate(self, tmp_path: Path) -> None:
        """
        Case where the list of studies contains a variant with an up-to-date snapshot and
        corresponds to a partial generation of commands for the variant (partially up-to-date)
        We expect to have a list of commands corresponding to the remaining commands.

        Given a list of descendants with some variants with up-to-date snapshots,
        When calling search_ref_study with the flag from_scratch=False,
        Then the variant is returned as reference study, and the remaining commands are returned.
        """
        root_study = create_study(id=str(uuid.uuid4()), name="root")

        # Prepare some variants with snapshots:
        variant1 = _create_variant(
            tmp_path,
            "variant1",
            root_study.id,
            datetime.datetime(year=2023, month=1, day=1),
            snapshot_created_at=datetime.datetime(year=2023, month=1, day=2),
        )

        # Add some variant commands
        variant1.commands = [
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant1.id,
                index=0,
                command="create_area",
                version=1,
                args='{"area_name": "DE"}',
            ),
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant1.id,
                index=1,
                command="create_thermal_cluster",
                version=1,
                args='{"area_name": "DE", "cluster_name": "DE", "cluster_type": "thermal"}',
            ),
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant1.id,
                index=2,
                command="update_thermal_clusters",
                version=1,
                args='{"cluster_properties": {"DE": {"DE": {"enabled": False}}}}',
            ),
        ]

        # The last executed command is the NOT last item of the commands list.
        variant1.snapshot.last_executed_command = variant1.commands[0].id

        # Check the variants
        references = [variant1]
        search_result = search_ref_study(root_study, references)
        assert search_result.ref_study == variant1
        assert search_result.cmd_blocks == variant1.commands[1:]
        assert search_result.force_regenerate is False

    def test_search_ref_study__missing_last_command(self, tmp_path: Path) -> None:
        """
        Case where the list of studies contains a variant with an up-to-date snapshot,
        but the last executed command is missing (probably caused by a bug).
        We expect to have the list of all variant commands, so that the snapshot can be re-generated.
        """
        root_study = create_study(id=str(uuid.uuid4()), name="root")

        # Prepare some variants with snapshots:
        variant1 = _create_variant(
            tmp_path,
            "variant1",
            root_study.id,
            datetime.datetime(year=2023, month=1, day=1),
            snapshot_created_at=datetime.datetime(year=2023, month=1, day=2),
        )

        # Add some variant commands
        variant1.commands = [
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant1.id,
                index=0,
                command="create_area",
                version=1,
                args='{"area_name": "DE"}',
            ),
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant1.id,
                index=1,
                command="create_thermal_cluster",
                version=1,
                args='{"area_name": "DE", "cluster_name": "DE", "cluster_type": "thermal"}',
            ),
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant1.id,
                index=2,
                command="update_thermal_clusters",
                version=1,
                args='{"cluster_properties": {"DE": {"DE": {"enabled": False}}}}',
            ),
        ]

        # The last executed command is missing.
        variant1.snapshot.last_executed_command = None

        # Check the variants
        references = [variant1]
        search_result = search_ref_study(root_study, references)
        assert search_result.ref_study == variant1
        assert search_result.cmd_blocks == variant1.commands
        assert search_result.force_regenerate is True

    def test_search_ref_study__deleted_last_command(self, tmp_path: Path) -> None:
        """
        Case where the list of studies contains a variant with an up-to-date snapshot,
        but the last executed command is missing (removed).
        We expect to have the list of all variant commands, so that the snapshot can be re-generated.
        """
        root_study = create_study(id=str(uuid.uuid4()), name="root")

        # Prepare some variants with snapshots:
        variant1 = _create_variant(
            tmp_path,
            "variant1",
            root_study.id,
            datetime.datetime(year=2023, month=1, day=1),
            snapshot_created_at=datetime.datetime(year=2023, month=1, day=2),
        )

        # Add some variant commands
        variant1.commands = [
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant1.id,
                index=0,
                command="create_area",
                version=1,
                args='{"area_name": "DE"}',
            ),
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant1.id,
                index=1,
                command="create_thermal_cluster",
                version=1,
                args='{"area_name": "DE", "cluster_name": "DE", "cluster_type": "thermal"}',
            ),
            CommandBlock(
                id=str(uuid.uuid4()),
                study_id=variant1.id,
                index=2,
                command="update_thermal_clusters",
                version=1,
                args='{"cluster_properties": {"DE": {"DE": {"enabled": False}}}}',
            ),
        ]

        # The last executed command is missing.
        variant1.snapshot.last_executed_command = str(uuid.uuid4())

        # Check the variants
        references = [variant1]
        search_result = search_ref_study(root_study, references)
        assert search_result.ref_study == variant1
        assert search_result.cmd_blocks == variant1.commands
        assert search_result.force_regenerate is True


class RegisterNotification(ITaskNotifier):
    """
    Callable used to register notifications.
    """

    def __init__(self) -> None:
        self.notifications: t.MutableSequence[str] = []

    def notify_message(self, notification: str) -> None:
        self.notifications.append(json.loads(notification))

    def notify_progress(self, progress: int) -> None:
        return


class FailingNotifier(ITaskNotifier):
    def __init__(self) -> None:
        pass

    def notify_message(self, notification: str) -> None:
        logger.warning("Something went wrong")

    def notify_progress(self, progress: int) -> None:
        return


class TestSnapshotGenerator:
    """
    Test the `SnapshotGenerator` class.
    """

    @pytest.fixture(name="jwt_user")
    def jwt_user_fixture(self) -> JWTUser:
        # Create a user in a "Writers" group:
        jwt_user = JWTUser(
            id=7,
            impersonator=7,
            type="users",
            groups=[JWTGroup(id="writers", name="Writers", role=RoleType.WRITER)],
        )
        # Ensure the user is in database.
        with db():
            role = Role(
                type=RoleType.WRITER,
                identity=User(id=jwt_user.id, name="john.doe"),
                group=Group(id="writers"),
            )
            db.session.add(role)
            db.session.commit()
        return jwt_user

    @pytest.fixture(name="root_study_id")
    def root_study_id_fixture(
        self,
        tmp_path: Path,
        raw_study_service: RawStudyService,
        variant_study_service: VariantStudyService,
        jwt_user: JWTUser,
    ) -> str:
        # Prepare a RAW study in the temporary folder
        study_dir = tmp_path / "my-study"
        root_study_id = str(uuid.uuid4())
        root_study = create_raw_study(
            id=root_study_id,
            workspace="default",
            path=str(study_dir),
            version="860",
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow(),
            additional_data=StudyAdditionalData(author="john.doe"),
            owner_id=jwt_user.id,
        )

        # Create the study in database
        root_study = raw_study_service.create(root_study)

        # Create some outputs with a "simulation.log" file
        for output_name in ["20230802-1425eco", "20230802-1628eco"]:
            output_dir = study_dir / "output" / output_name
            output_dir.mkdir(parents=True)
            (output_dir / "simulation.log").touch()

        with db():
            # Save the root study in database
            variant_study_service.repository.save(root_study)
        return root_study_id

    @pytest.fixture(name="variant_study")
    def variant_study_fixture(
        self,
        root_study_id: str,
        variant_study_service: VariantStudyService,
        jwt_user: JWTUser,
    ) -> VariantStudy:
        with db():
            # Create un new variant
            name = "my-variant"
            with current_user_context(jwt_user):
                variant_study = variant_study_service.create_variant_study(root_study_id, name)
            study_version = StudyVersion.parse(variant_study.version)

            # Append some commands
            with current_user_context(jwt_user):
                variant_study_service.append_commands(
                    variant_study.id,
                    [
                        CommandDTO(action="create_area", args={"area_name": "North"}, study_version=study_version),
                        CommandDTO(action="create_area", args={"area_name": "South"}, study_version=study_version),
                        CommandDTO(
                            action="create_link", args={"area1": "north", "area2": "south"}, study_version=study_version
                        ),
                        CommandDTO(
                            action="create_cluster",
                            args={
                                "area_id": "south",
                                "cluster_name": "gas_cluster",
                                "parameters": {"group": "Gas", "unitcount": 1, "nominalcapacity": 500},
                            },
                            study_version=study_version,
                        ),
                    ],
                )
            return variant_study

    def test_init(self, variant_study_service: VariantStudyService) -> None:
        """
        Test the initialization of the `SnapshotGenerator` class.
        """
        generator = SnapshotGenerator(
            cache=variant_study_service.cache,
            raw_study_service=variant_study_service.raw_study_service,
            command_factory=variant_study_service.command_factory,
            study_factory=variant_study_service.study_factory,
            repository=variant_study_service.repository,
        )
        assert generator.cache == variant_study_service.cache
        assert generator.raw_study_service == variant_study_service.raw_study_service
        assert generator.command_factory == variant_study_service.command_factory
        assert generator.study_factory == variant_study_service.study_factory
        assert generator.repository == variant_study_service.repository

    @with_admin_user
    @with_db_context
    def test_generate__nominal_case(
        self, variant_study: VariantStudy, variant_study_service: VariantStudyService
    ) -> None:
        """
        Test the generation of a variant study based on a raw study.

        Given a raw study and a single variant study,
        When calling generate with:
        - `denormalize` set to False,
        - `from_scratch` set to False,
        - `notifier` set to a callback function used to register de notifications,
        Then the variant generation must succeed.
        We must check that:
        - the number of database queries is kept as low as possible,
        - the variant is correctly generated in the "snapshot" directory and all commands are applied,
        - the matrices are not denormalized (we should have links to matrices),
        - the variant is updated in the database (snapshot and additional_data),
        - the cache is updated with the new variant configuration,
        - the temporary directory is correctly removed.
        - the notifications are correctly registered.
        - the simulation outputs are not copied.
        """
        generator = SnapshotGenerator(
            cache=variant_study_service.cache,
            raw_study_service=variant_study_service.raw_study_service,
            command_factory=variant_study_service.command_factory,
            study_factory=variant_study_service.study_factory,
            repository=variant_study_service.repository,
        )

        notifier = RegisterNotification()

        with DBStatementRecorder(db.session.bind) as db_recorder:
            results = generator.generate_snapshot(
                variant_study.id,
                denormalize=False,
                from_scratch=False,
                notifier=notifier,
            )

        # Check: the number of database queries is kept as low as possible.
        # We expect 6 queries:
        # - 1 query to fetch the ancestors of a variant study,
        # - 1 query to fetch the root study (with owner and groups for permission check),
        # - 1 query to fetch the list of variants with snapshot, commands, etc.,
        # - 1 query to fetch raw study information,
        # - 1 query to update the variant study additional_data,
        # - 1 query to insert the variant study snapshot.
        assert len(db_recorder.sql_statements) == 6, str(db_recorder)

        # Check: the variant generation must succeed.
        assert results.model_dump() == {
            "success": True,
            "should_invalidate_cache": False,
            "details": [
                {
                    "id": AnyUUID(),
                    "name": "create_area",
                    "status": True,
                    "msg": "Area 'North' created",
                },
                {
                    "id": AnyUUID(),
                    "name": "create_area",
                    "status": True,
                    "msg": "Area 'South' created",
                },
                {
                    "id": AnyUUID(),
                    "name": "create_link",
                    "status": True,
                    "msg": "Link between 'north' and 'south' created",
                },
                {
                    "id": AnyUUID(),
                    "name": "create_cluster",
                    "status": True,
                    "msg": "Thermal cluster 'gas_cluster' added to area 'south'.",
                },
            ],
        }

        # Check: the variant is correctly generated and all commands are applied.
        snapshot_dir = variant_study.snapshot_dir
        assert snapshot_dir.exists()
        assert (snapshot_dir / "study.antares").exists()
        assert (snapshot_dir / "input/areas/list.txt").read_text().splitlines(keepends=False) == ["North", "South"]
        reader = IniReader()
        properties = reader.read(snapshot_dir / "input/links/north/properties.ini")
        assert list(properties.keys()) == ["south"]
        reader = IniReader()
        cluster_props = reader.read(snapshot_dir / "input/thermal/clusters/south/list.ini")
        assert list(cluster_props.keys()) == ["gas_cluster"]
        assert cluster_props["gas_cluster"] == {
            "co2": 0.0,
            "enabled": True,
            "fixed-cost": 0.0,
            "gen-ts": "use global",
            "group": "gas",
            "law.forced": "uniform",
            "law.planned": "uniform",
            "marginal-cost": 0.0,
            "market-bid-cost": 0.0,
            "min-down-time": 1,
            "min-stable-power": 0.0,
            "min-up-time": 1,
            "must-run": False,
            "name": "gas_cluster",
            "nh3": 0.0,
            "nmvoc": 0.0,
            "nominalcapacity": 500.0,
            "nox": 0.0,
            "op1": 0.0,
            "op2": 0.0,
            "op3": 0.0,
            "op4": 0.0,
            "op5": 0.0,
            "pm10": 0.0,
            "pm2_5": 0.0,
            "pm5": 0.0,
            "so2": 0.0,
            "spinning": 0.0,
            "spread-cost": 0.0,
            "startup-cost": 0.0,
            "unitcount": 1,
            "volatility.forced": 0.0,
            "volatility.planned": 0.0,
        }

        # Check: the matrices are not denormalized (we should have links to matrices).
        assert (snapshot_dir / "input/links/north/south_parameters.txt.link").exists()
        assert (snapshot_dir / "input/thermal/series/south/gas_cluster/series.txt.link").exists()

        # Check: the variant is updated in the database (snapshot and additional_data).
        with db():
            study = variant_study_service.repository.get(variant_study.id)
            assert study is not None
            assert study.snapshot is not None
            assert study.snapshot.last_executed_command == study.commands[-1].id
            assert study.additional_data.author == "john.doe"

        # Check: the cache is updated with the new variant configuration.
        # The cache is a mock created in the session's scope, so it is shared between all tests.
        cache: Mock = generator.cache  # type: ignore
        # So, the number of calls to the `put` method is at least equal to 2.
        assert cache.put.call_count >= 2
        # The last call to the `put` method is for the variant study.
        put_variant = cache.put.call_args_list[-1]
        assert put_variant[0][0] == f"{CacheConstants.STUDY_FACTORY}/{variant_study.id}"
        variant_study_config = put_variant[0][1]
        assert variant_study_config["study_id"] == variant_study.id

        # Check: the temporary directory is correctly removed.
        assert list(snapshot_dir.parent.iterdir()) == [snapshot_dir]

        # Check: the notifications are correctly registered.
        assert notifier.notifications == [
            {
                "details": [
                    {
                        "id": AnyUUID(as_string=True),
                        "msg": "Area 'North' created",
                        "name": "create_area",
                        "status": True,
                    },
                    {
                        "id": AnyUUID(as_string=True),
                        "msg": "Area 'South' created",
                        "name": "create_area",
                        "status": True,
                    },
                    {
                        "id": AnyUUID(as_string=True),
                        "msg": "Link between 'north' and 'south' created",
                        "name": "create_link",
                        "status": True,
                    },
                    {
                        "id": AnyUUID(as_string=True),
                        "msg": "Thermal cluster 'gas_cluster' added to area 'south'.",
                        "name": "create_cluster",
                        "status": True,
                    },
                ],
                "success": True,
                "should_invalidate_cache": False,
            }
        ]

        # Check: the simulation outputs are not copied.
        assert not (snapshot_dir / "output").exists()

    @with_admin_user
    @with_db_context
    def test_generate__with_denormalize_true(
        self, variant_study: VariantStudy, variant_study_service: VariantStudyService
    ) -> None:
        """
        Test the generation of a variant study with matrices de-normalization.
        We expect that all matrices are correctly denormalized (no link).
        """
        generator = SnapshotGenerator(
            cache=variant_study_service.cache,
            raw_study_service=variant_study_service.raw_study_service,
            command_factory=variant_study_service.command_factory,
            study_factory=variant_study_service.study_factory,
            repository=variant_study_service.repository,
        )

        results = generator.generate_snapshot(
            variant_study.id,
            denormalize=True,
            from_scratch=False,
        )

        # Check the results
        assert results.model_dump() == {
            "success": True,
            "should_invalidate_cache": False,
            "details": [
                {
                    "id": AnyUUID(),
                    "name": "create_area",
                    "status": True,
                    "msg": "Area 'North' created",
                },
                {
                    "id": AnyUUID(),
                    "name": "create_area",
                    "status": True,
                    "msg": "Area 'South' created",
                },
                {
                    "id": AnyUUID(),
                    "name": "create_link",
                    "status": True,
                    "msg": "Link between 'north' and 'south' created",
                },
                {
                    "id": AnyUUID(),
                    "name": "create_cluster",
                    "status": True,
                    "msg": "Thermal cluster 'gas_cluster' added to area 'south'.",
                },
            ],
        }

        # Check: the matrices are denormalized (we should have TSV files).
        snapshot_dir = variant_study.snapshot_dir
        assert (snapshot_dir / "input/links/north/south_parameters.txt").exists()
        array = np.loadtxt(snapshot_dir / "input/links/north/south_parameters.txt", delimiter="\t")
        assert array.shape == (8760, 6)

        assert (snapshot_dir / "input/thermal/series/south/gas_cluster/series.txt").exists()
        array = np.loadtxt(snapshot_dir / "input/thermal/series/south/gas_cluster/series.txt", delimiter="\t")
        assert array.size == 0

    @with_admin_user
    @with_db_context
    def test_generate__with_invalid_command(
        self, variant_study: VariantStudy, variant_study_service: VariantStudyService
    ) -> None:
        """
        Test the generation of a variant study with an invalid command.
        We expect to have a clear error message explaining which command fails.
        The snapshot directory must be removed (and no temporary directory must be left).
        """
        # Append an invalid command to the variant study.
        study_version = StudyVersion.parse(variant_study.version)
        variant_study_service.append_commands(
            variant_study.id,
            [
                CommandDTO(action="create_area", args={"area_name": "North"}, study_version=study_version),  # duplicate
            ],
        )

        generator = SnapshotGenerator(
            cache=variant_study_service.cache,
            raw_study_service=variant_study_service.raw_study_service,
            command_factory=variant_study_service.command_factory,
            study_factory=variant_study_service.study_factory,
            repository=variant_study_service.repository,
        )

        err_msg = (
            f"Failed to generate variant study {variant_study.id}: Area 'North' already exists and could not be created"
        )
        with pytest.raises(VariantGenerationError, match=re.escape(err_msg)):
            generator.generate_snapshot(
                variant_study.id,
                denormalize=False,
                from_scratch=False,
            )

        # Check: the snapshot directory is removed.
        snapshot_dir = variant_study.snapshot_dir
        assert not snapshot_dir.exists()

        # Check: no temporary directory is left.
        assert list(snapshot_dir.parent.iterdir()) == []

    @with_admin_user
    @with_db_context
    def test_generate__notification_failure(
        self,
        variant_study: VariantStudy,
        variant_study_service: VariantStudyService,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """
        Test the generation of a variant study with a notification that fails.
        Since the notification is not critical, we expect to have no exception.
        """
        generator = SnapshotGenerator(
            cache=variant_study_service.cache,
            raw_study_service=variant_study_service.raw_study_service,
            command_factory=variant_study_service.command_factory,
            study_factory=variant_study_service.study_factory,
            repository=variant_study_service.repository,
        )

        notifier = FailingNotifier()

        with caplog.at_level(logging.WARNING):
            results = generator.generate_snapshot(
                variant_study.id,
                denormalize=False,
                from_scratch=False,
                notifier=notifier,
            )

        # Check the results
        assert results.model_dump() == {
            "success": True,
            "should_invalidate_cache": False,
            "details": [
                {
                    "id": AnyUUID(),
                    "name": "create_area",
                    "status": True,
                    "msg": "Area 'North' created",
                },
                {
                    "id": AnyUUID(),
                    "name": "create_area",
                    "status": True,
                    "msg": "Area 'South' created",
                },
                {
                    "id": AnyUUID(),
                    "name": "create_link",
                    "status": True,
                    "msg": "Link between 'north' and 'south' created",
                },
                {
                    "id": AnyUUID(),
                    "name": "create_cluster",
                    "status": True,
                    "msg": "Thermal cluster 'gas_cluster' added to area 'south'.",
                },
            ],
        }

        # Check th logs
        assert "Something went wrong" in caplog.text

    @with_admin_user
    @with_db_context
    def test_generate__variant_of_variant(
        self,
        variant_study: VariantStudy,
        variant_study_service: VariantStudyService,
    ) -> None:
        """
        Test the generation of a variant study of a variant study.
        """
        generator = SnapshotGenerator(
            cache=variant_study_service.cache,
            raw_study_service=variant_study_service.raw_study_service,
            command_factory=variant_study_service.command_factory,
            study_factory=variant_study_service.study_factory,
            repository=variant_study_service.repository,
        )

        # Generate the variant once.
        generator.generate_snapshot(
            variant_study.id,
            denormalize=False,
            from_scratch=False,
        )

        # Create a new variant of the variant study
        new_variant = variant_study_service.create_variant_study(variant_study.id, "my-variant")

        # Append some commands to the new variant.
        study_version = StudyVersion.parse(new_variant.version)
        variant_study_service.append_commands(
            new_variant.id,
            [
                CommandDTO(action="create_area", args={"area_name": "East"}, study_version=study_version),
            ],
        )

        # Generate the variant again.
        results = generator.generate_snapshot(
            new_variant.id,
            denormalize=False,
            from_scratch=False,
        )

        # Check the results
        assert results.model_dump() == {
            "success": True,
            "should_invalidate_cache": False,
            "details": [
                {
                    "id": AnyUUID(),
                    "name": "create_area",
                    "status": True,
                    "msg": "Area 'East' created",
                },
            ],
        }

    @with_admin_user
    @with_db_context
    def test_generate_invalidate_cache(
        self, variant_study_service: VariantStudyService, variant_study: VariantStudy
    ) -> None:
        cache = LocalCache()
        variant_study_service.cache = cache
        generator = SnapshotGenerator(
            cache=cache,
            raw_study_service=variant_study_service.raw_study_service,
            command_factory=variant_study_service.command_factory,
            study_factory=variant_study_service.study_factory,
            repository=variant_study_service.repository,
        )

        # Fill the cache for the test.
        study = db.session.query(VariantStudy).get(variant_study.id)  #  `variant_study` isn't bound to the session yet.
        study_interface = VariantStudyInterface(variant_study_service, study)
        file_study = study_interface.get_files()
        data = FileStudyTreeConfigDTO.from_build_config(file_study.config).model_dump()
        update_cache(cache, variant_study.id, data)

        # Checks the cache content
        cache_key = f"{CacheConstants.STUDY_FACTORY}/{variant_study.id}"
        assert cache.get(cache_key) is not None
        starting_cache = cache.get(cache_key)
        assert starting_cache is not None
        # Performs a little modification in memory for the next tests
        starting_cache["output_path"] = starting_cache["output_path"].parent / "snapshot" / "output"

        # Generates the snapshot
        results = generator.generate_snapshot(variant_study.id, denormalize=False)
        # Ensures we shouldn't have to invalidate the cache as all commands updated the config correctly
        assert not results.should_invalidate_cache
        assert cache.get(cache_key) == starting_cache

        # Add an `update_config` command
        version = StudyVersion.parse(variant_study.version)
        variant_study_service.append_commands(
            variant_study.id,
            [
                CommandDTO(
                    action="update_config",
                    args={
                        "target": "input/areas/north/optimization/filtering/filter_synthesis",
                        "data": "annual",
                    },
                    study_version=version,
                )
            ],
        )

        results = generator.generate_snapshot(variant_study.id, denormalize=False)
        # Ensures we have to invalidate the cache as the `update_config` command couldn't (it's too generic)
        assert results.should_invalidate_cache
        assert cache.get(cache_key) is None
