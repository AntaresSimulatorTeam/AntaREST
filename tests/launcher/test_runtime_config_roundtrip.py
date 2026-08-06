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

from pathlib import Path
from unittest.mock import Mock

from antarest.core.config import Config, LauncherConfig, LocalConfig, SlurmConfig, StorageConfig
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.launcher.model import LauncherRuntimeConfig, SlurmRuntimeConfig, SlurmRuntimeConfigDB
from antarest.launcher.repository import LauncherRuntimeConfigRepository
from antarest.launcher.service import LauncherService
from antarest.login.utils import current_user_context
from tests.helpers import with_db_context


def _build_service(tmp_path: Path) -> LauncherService:
    config = Config(
        storage=StorageConfig(tmp_dir=tmp_path),
        launcher=LauncherConfig(
            default="local",
            configs=[LocalConfig(id="local", name="local"), SlurmConfig(id="slurm", name="slurm")],
        ),
    )
    factory_launcher_mock = Mock()
    factory_launcher_mock.build_launcher.return_value = {"local": Mock(), "slurm": Mock()}

    return LauncherService(
        config=config,
        study_service=Mock(),
        output_service=Mock(),
        login_service=Mock(),
        job_result_repository=Mock(),
        solver_presets_repository=Mock(),
        launcher_runtime_config_repository=LauncherRuntimeConfigRepository(),  # real repo, real DB
        launcher_load_repository=Mock(),
        factory_launcher=factory_launcher_mock,
        event_bus=Mock(),
        file_transfer_manager=Mock(),
        task_service=Mock(),
        cache=Mock(),
    )


@with_db_context
def test_get_put_round_trips_on_non_slurm_launcher(tmp_path: Path) -> None:
    service = _build_service(tmp_path)

    with current_user_context(DEFAULT_ADMIN_USER):
        # 1. Store an empty config on the (non-SLURM) local launcher.
        service.update_runtime_config("local", LauncherRuntimeConfig())

        # 2. Read it back -> no SLURM section.
        fetched = service.get_runtime_config("local")
        assert fetched.slurm is None

        # 3. PUT the exact GET payload back on the same launcher. This must round-trip cleanly.
        service.update_runtime_config("local", fetched)


@with_db_context
def test_clearing_config_removes_the_row(tmp_path: Path) -> None:
    """
    Full-replace honesty: a row exists iff there is real config. Clearing the config (PUT with no
    SLURM content) deletes the stored row instead of leaving a meaningless NULL-threshold row.
    """
    service = _build_service(tmp_path)

    with current_user_context(DEFAULT_ADMIN_USER):
        # Set a real threshold on the SLURM launcher -> a row is stored.
        service.update_runtime_config(
            "slurm", LauncherRuntimeConfig(slurm=SlurmRuntimeConfig(oversubscribe_core_threshold=8))
        )
        assert db.session.get(SlurmRuntimeConfigDB, "slurm") is not None

        # Clear it -> the row is removed, not kept as a NULL-threshold row.
        service.update_runtime_config("slurm", LauncherRuntimeConfig())
        assert db.session.get(SlurmRuntimeConfigDB, "slurm") is None
        assert service.get_runtime_config("slurm").slurm is None
