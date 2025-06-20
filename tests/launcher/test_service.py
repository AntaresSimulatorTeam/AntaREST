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
import math
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Union
from unittest.mock import Mock, call
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile

import pytest
from sqlalchemy import create_engine

from antarest.core.config import (
    Config,
    InvalidConfigurationError,
    LauncherConfig,
    LocalConfig,
    NbCoresConfig,
    SlurmConfig,
    StorageConfig,
)
from antarest.core.exceptions import StudyNotFoundError
from antarest.core.filetransfer.model import FileDownload, FileDownloadDTO, FileDownloadTaskDTO
from antarest.core.interfaces.cache import ICache
from antarest.core.interfaces.eventbus import Event, EventType
from antarest.core.jwt import DEFAULT_ADMIN_USER, JWTUser
from antarest.core.model import PermissionInfo
from antarest.core.requests import UserHasNotPermissionError
from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware
from antarest.dbmodel import Base
from antarest.launcher.model import (
    JobLog,
    JobLogType,
    JobResult,
    JobStatus,
    LauncherLoadDTO,
    LauncherParametersDTO,
    LogType,
)
from antarest.launcher.service import EXECUTION_INFO_FILE, LAUNCHER_PARAM_NAME_SUFFIX, JobNotFound, LauncherService
from antarest.login.model import Identity
from antarest.login.utils import current_user_context, get_current_user
from antarest.study.model import STUDY_VERSION_8_8, OwnerInfo, PublicMode, Study, StudyMetadataDTO
from antarest.study.repository import StudyMetadataRepository
from antarest.study.service import StudyService
from antarest.study.storage.output_service import OutputService
from tests.helpers import with_admin_user


class TestLauncherService:
    @with_admin_user
    @pytest.mark.unit_test
    def test_service_run_study(self) -> None:
        storage_service_mock = Mock()
        # noinspection SpellCheckingInspection
        storage_service_mock.get_study_information.return_value = StudyMetadataDTO(
            id="id",
            name="name",
            created="1",
            updated="1",
            type="rawstudy",
            owner=OwnerInfo(id=0, name="author"),
            groups=[],
            public_mode=PublicMode.NONE,
            version=STUDY_VERSION_8_8,
            workspace="default",
            managed=True,
            archived=False,
        )
        storage_service_mock.get_study_path.return_value = Path("path/to/study")

        uuid = uuid4()
        launcher_mock = Mock()
        factory_launcher_mock = Mock()
        factory_launcher_mock.build_launcher.return_value = {"local": launcher_mock}

        event_bus = Mock()

        pending = JobResult(
            id=str(uuid),
            study_id="study_uuid",
            job_status=JobStatus.PENDING,
            launcher="local",
            launcher_params=LauncherParametersDTO().model_dump_json(),
        )
        repository = Mock()
        repository.save.return_value = pending

        launcher_service = LauncherService(
            config=Config(),
            study_service=storage_service_mock,
            output_service=OutputService(storage_service_mock, Mock(), Mock(), Mock(), event_bus),
            login_service=Mock(),
            job_result_repository=repository,
            factory_launcher=factory_launcher_mock,
            event_bus=event_bus,
            file_transfer_manager=Mock(),
            task_service=Mock(),
            cache=Mock(),
        )
        launcher_service._generate_new_id = lambda: str(uuid)

        storage_service_mock.get_user_name.return_value = "fake_user"
        job_id = launcher_service.run_study("study_uuid", "local", LauncherParametersDTO())

        assert job_id == str(uuid)

        repository.save.assert_called_once()

        # SQLAlchemy provides its own way to handle object comparison, which ensures
        # that the comparison is based on the database identity of the objects.
        # But, here, in that unit test, objects are not in a database session,
        # so we need to compare them manually.
        mock_call = repository.save.mock_calls[0]
        actual_obj: JobResult = mock_call.args[0]
        assert actual_obj.to_dto().model_dump() == pending.to_dto().model_dump()

        event_bus.push.assert_called_once_with(
            Event(
                type=EventType.STUDY_JOB_STARTED,
                payload=pending.to_dto().model_dump(),
                permissions=PermissionInfo(owner=0),
            )
        )

    @with_admin_user
    @pytest.mark.unit_test
    def test_service_get_result_from_launcher(self) -> None:
        launcher_mock = Mock()
        fake_execution_result = JobResult(
            id=str(uuid4()),
            study_id="sid",
            job_status=JobStatus.SUCCESS,
            msg="Hello, World!",
            exit_code=0,
            launcher="local",
            owner_id=1,
        )
        factory_launcher_mock = Mock()
        factory_launcher_mock.build_launcher.return_value = {"local": launcher_mock}

        repository = Mock()
        repository.get.return_value = fake_execution_result

        study_service = Mock()
        study_service.get_study.return_value = Mock(spec=Study, groups=[], owner=None, public_mode=PublicMode.NONE)

        launcher_service = LauncherService(
            config=Config(),
            study_service=study_service,
            output_service=OutputService(study_service, Mock(), Mock(), Mock(), Mock()),
            login_service=Mock(),
            job_result_repository=repository,
            factory_launcher=factory_launcher_mock,
            event_bus=Mock(),
            file_transfer_manager=Mock(),
            task_service=Mock(),
            cache=Mock(),
        )

        job_id = uuid4()
        assert launcher_service.get_result(job_uuid=job_id) == fake_execution_result

    @with_admin_user
    @pytest.mark.unit_test
    def test_service_get_result_from_database(self) -> None:
        launcher_mock = Mock()
        fake_execution_result = JobResult(
            id=str(uuid4()),
            study_id="sid",
            job_status=JobStatus.SUCCESS,
            msg="Hello, World!",
            exit_code=0,
            owner_id=1,
        )
        launcher_mock.get_result.return_value = None
        factory_launcher_mock = Mock()
        factory_launcher_mock.build_launcher.return_value = {"local": launcher_mock}

        repository = Mock()
        repository.get.return_value = fake_execution_result

        study_service = Mock()
        study_service.get_study.return_value = Mock(spec=Study, groups=[], owner=None, public_mode=PublicMode.NONE)

        launcher_service = LauncherService(
            config=Config(),
            study_service=study_service,
            output_service=OutputService(study_service, Mock(), Mock(), Mock(), Mock()),
            login_service=Mock(),
            job_result_repository=repository,
            factory_launcher=factory_launcher_mock,
            event_bus=Mock(),
            file_transfer_manager=Mock(),
            task_service=Mock(),
            cache=Mock(),
        )

        assert launcher_service.get_result(job_uuid=uuid4()) == fake_execution_result

    @pytest.mark.unit_test
    def test_service_get_jobs_from_database(self, db_session) -> None:
        launcher_mock = Mock()
        now = datetime.utcnow()
        identity_instance = Identity(id=1)
        fake_execution_result = [
            JobResult(
                id=str(uuid4()),
                study_id="a",
                job_status=JobStatus.SUCCESS,
                msg="Hello, World!",
                exit_code=0,
                owner=identity_instance,
            )
        ]
        returned_faked_execution_results = [
            JobResult(
                id="1",
                study_id="a",
                job_status=JobStatus.SUCCESS,
                msg="Hello, World!",
                exit_code=0,
                creation_date=now,
                owner=identity_instance,
            ),
            JobResult(
                id="2",
                study_id="b",
                job_status=JobStatus.SUCCESS,
                msg="Hello, World!",
                exit_code=0,
                creation_date=now,
                owner=identity_instance,
            ),
        ]
        all_faked_execution_results = returned_faked_execution_results + [
            JobResult(
                id="3",
                study_id="c",
                job_status=JobStatus.SUCCESS,
                msg="Hello, World!",
                exit_code=0,
                creation_date=now - timedelta(days=11),
                owner=identity_instance,
            )
        ]
        launcher_mock.get_result.return_value = None
        factory_launcher_mock = Mock()
        factory_launcher_mock.build_launcher.return_value = {"local": launcher_mock}

        repository = Mock()
        repository.find_by_study.return_value = fake_execution_result
        repository.get_all.return_value = all_faked_execution_results

        study_service = Mock(spec=StudyService)
        study_service.repository = StudyMetadataRepository(cache_service=Mock(spec=ICache), session=db_session)
        db_session.add_all(fake_execution_result)
        db_session.add_all(all_faked_execution_results)
        db_session.commit()

        launcher_service = LauncherService(
            config=Config(),
            study_service=study_service,
            output_service=OutputService(study_service, Mock(), Mock(), Mock(), Mock()),
            login_service=Mock(),
            job_result_repository=repository,
            factory_launcher=factory_launcher_mock,
            event_bus=Mock(),
            file_transfer_manager=Mock(),
            task_service=Mock(),
            cache=Mock(),
        )

        study_id = uuid4()

        with current_user_context(DEFAULT_ADMIN_USER):
            assert launcher_service.get_jobs(str(study_id)) == fake_execution_result
            repository.find_by_study.assert_called_once_with(str(study_id))
            assert launcher_service.get_jobs(None) == all_faked_execution_results

        jwt_user = JWTUser(id=2, impersonator=2, type="users", groups=[])
        with current_user_context(jwt_user):
            assert launcher_service.get_jobs(None) == []

        with pytest.raises(UserHasNotPermissionError):
            with current_user_context(jwt_user):
                launcher_service.remove_job("some job")

        with current_user_context(DEFAULT_ADMIN_USER):
            launcher_service.remove_job("some job")
        repository.delete.assert_called_with("some job")

    @pytest.mark.unit_test
    @pytest.mark.parametrize(
        "config, solver, expected",
        [
            pytest.param(
                {
                    "default": "local_id",
                    "launchers": [
                        {"id": "local_id", "type": "local", "name": "name", "binaries": {}},
                        {"id": "slurm_id", "type": "slurm", "name": "name", "antares_versions_on_remote_server": []},
                    ],
                },
                None,
                [],
                id="empty-config",
            ),
            pytest.param(
                {
                    "default": "local_id",
                    "launchers": [
                        {
                            "id": "local_id",
                            "type": "local",
                            "name": "name",
                            "binaries": {"456": "path", "123": "path", "798": "path"},
                        }
                    ],
                },
                None,
                ["123", "456", "798"],
                id="local-config-default",
            ),
            pytest.param(
                {
                    "default": "local_id",
                    "launchers": [
                        {
                            "id": "local_id",
                            "type": "local",
                            "name": "name",
                            "binaries": {"456": "path", "123": "path", "798": "path"},
                        }
                    ],
                },
                "unknown",
                [],
                id="local-config-slurm",
                marks=pytest.mark.xfail(
                    reason="Unknown solver configuration: 'unknown'",
                    raises=InvalidConfigurationError,
                    strict=True,
                ),
            ),
            pytest.param(
                {
                    "default": "local_id",
                    "launchers": [
                        {
                            "id": "local_id",
                            "type": "local",
                            "name": "name",
                            "binaries": {"456": "path", "123": "path", "798": "path"},
                        }
                    ],
                },
                "unknown",
                [],
                id="local-config-unknown",
                marks=pytest.mark.xfail(
                    reason="Unknown solver configuration: 'unknown'",
                    raises=InvalidConfigurationError,
                    strict=True,
                ),
            ),
            pytest.param(
                {
                    "default": "slurm_id",
                    "launchers": [
                        {
                            "id": "slurm_id",
                            "type": "slurm",
                            "name": "name",
                            "antares_versions_on_remote_server": ["258", "147", "369"],
                        }
                    ],
                },
                None,
                ["147", "258", "369"],
                id="slurm-config-default",
            ),
            pytest.param(
                {
                    "default": "slurm_id",
                    "launchers": [
                        {
                            "id": "slurm_id",
                            "type": "slurm",
                            "name": "name",
                            "antares_versions_on_remote_server": ["258", "147", "369"],
                        }
                    ],
                },
                "local_id",
                [],
                id="slurm-config-local",
                marks=pytest.mark.xfail(
                    reason="Unknown solver configuration: 'unknown'",
                    raises=InvalidConfigurationError,
                    strict=True,
                ),
            ),
            pytest.param(
                {
                    "default": "slurm_id",
                    "launchers": [
                        {
                            "id": "slurm_id",
                            "type": "slurm",
                            "name": "name",
                            "antares_versions_on_remote_server": ["258", "147", "369"],
                        }
                    ],
                },
                "unknown",
                [],
                id="slurm-config-unknown",
                marks=pytest.mark.xfail(
                    reason="Unknown solver configuration: 'unknown'",
                    raises=InvalidConfigurationError,
                    strict=True,
                ),
            ),
            pytest.param(
                {
                    "default": "slurm_id",
                    "launchers": [
                        {
                            "id": "local_id",
                            "type": "local",
                            "name": "name",
                            "binaries": {"456": "path", "123": "path", "798": "path"},
                        },
                        {
                            "id": "slurm_id",
                            "type": "slurm",
                            "name": "name",
                            "antares_versions_on_remote_server": ["258", "147", "369"],
                        },
                    ],
                },
                "local_id",
                ["123", "456", "798"],
                id="local+slurm-config-local",
            ),
            pytest.param(
                {
                    "default": "default",
                    "launchers": [
                        {
                            "id": "local_id",
                            "type": "local",
                            "name": "name",
                            "binaries": {"456": "path", "123": "path", "798": "path"},
                        }
                    ],
                },
                "",
                [],
                id="default-config-not-found",
                marks=pytest.mark.xfail(
                    reason="Default launcher id default not found in launcher configs",
                    raises=InvalidConfigurationError,
                    strict=True,
                ),
            ),
        ],
    )
    def test_service_get_solver_versions(
        self,
        config: Dict[str, Union[str, List[Dict[str, Union[str, Dict[str, str]]]]]],
        solver: str,
        expected: List[str],
    ) -> None:
        launcher_configs = []
        for launcher in config["launchers"]:
            if launcher["type"] == "local":
                launcher_configs.append(
                    LocalConfig(
                        id=launcher["id"],
                        name=launcher["name"],
                        binaries={k: Path(f"solver-{k}.exe") for k in launcher.get("binaries", {})},
                    )
                )
            elif launcher["type"] == "slurm":
                launcher_configs.append(
                    SlurmConfig(
                        id=launcher["id"],
                        name=launcher["name"],
                        antares_versions_on_remote_server=list(launcher.get("antares_versions_on_remote_server", [])),
                    )
                )

        launcher_config = LauncherConfig(default=config["default"], configs=launcher_configs)

        full_config = Config(launcher=launcher_config)

        mock_launcher = Mock()
        mock_launcher.get_solver_versions.return_value = expected

        mock_launchers = {}
        for launcher in config["launchers"]:
            if launcher["id"] == config["default"] or launcher["id"] == solver:
                mock_launchers[launcher["id"]] = mock_launcher

        mock_factory = Mock()
        mock_factory.build_launcher.return_value = mock_launchers

        launcher_service = LauncherService(
            config=full_config,
            study_service=Mock(),
            output_service=Mock(),
            login_service=Mock(),
            job_result_repository=Mock(),
            factory_launcher=mock_factory,
            event_bus=Mock(),
            file_transfer_manager=Mock(),
            task_service=Mock(),
            cache=Mock(),
        )

        actual = launcher_service.get_solver_versions(solver)
        assert actual == expected

    @pytest.mark.unit_test
    @pytest.mark.parametrize(
        "config_map, solver, expected",
        [
            pytest.param(
                {"default": "local_id", "launchers": []},
                None,
                {},
                id="empty-config",
                marks=pytest.mark.xfail(
                    raises=InvalidConfigurationError,
                    strict=True,
                    reason="Configuration is not available for the 'local_id' launcher",
                ),
            ),
            pytest.param(
                {
                    "default": "local_id",
                    "launchers": [
                        {
                            "id": "local_id",
                            "type": "local",
                            "nb_cores": {"min": 1, "default": 11, "max": 12},
                        }
                    ],
                },
                None,
                {"min": 1, "default": 11, "max": 12},
                id="local-config-default",
            ),
            pytest.param(
                {
                    "default": "local_id",
                    "launchers": [
                        {
                            "id": "local_id",
                            "type": "local",
                            "nb_cores": {"min": 1, "default": 11, "max": 12},
                        }
                    ],
                },
                None,
                {"min": 1, "default": 11, "max": 12},
                id="local-config-slurm",
            ),
            pytest.param(
                {
                    "default": "local_id",
                    "launchers": [
                        {
                            "id": "local_id",
                            "type": "local",
                            "nb_cores": {"min": 1, "default": 11, "max": 12},
                        }
                    ],
                },
                None,
                {"min": 1, "default": 11, "max": 12},
                id="local-config-unknown",
            ),
            pytest.param(
                {
                    "default": "slurm_id",
                    "launchers": [
                        {
                            "id": "slurm_id",
                            "type": "slurm",
                            "nb_cores": {"min": 4, "default": 8, "max": 16},
                        }
                    ],
                },
                None,
                {"min": 4, "default": 8, "max": 16},
                id="slurm-config-default",
            ),
            pytest.param(
                {
                    "default": "slurm_id",
                    "launchers": [
                        {
                            "id": "slurm_id",
                            "type": "slurm",
                            "nb_cores": {"min": 4, "default": 8, "max": 16},
                        }
                    ],
                },
                None,
                {"min": 4, "default": 8, "max": 16},
                id="slurm-config-local",
            ),
            pytest.param(
                {
                    "default": "slurm_id",
                    "launchers": [
                        {
                            "id": "slurm_id",
                            "type": "slurm",
                            "nb_cores": {"min": 4, "default": 8, "max": 16},
                        }
                    ],
                },
                None,
                {"min": 4, "default": 8, "max": 16},
                id="slurm-config-unknown",
            ),
            pytest.param(
                {
                    "default": "slurm_id",
                    "launchers": [
                        {
                            "id": "local_id",
                            "type": "local",
                            "nb_cores": {"min": 1, "default": 11, "max": 12},
                        },
                        {
                            "id": "slurm_id",
                            "type": "slurm",
                            "nb_cores": {"min": 4, "default": 8, "max": 16},
                        },
                    ],
                },
                "local_id",
                {"min": 1, "default": 11, "max": 12},
                id="local+slurm-config-local",
            ),
        ],
    )
    def test_get_nb_cores(
        self,
        config_map: Dict[str, Union[str, List[Dict[str, Any]]]],
        solver: str,
        expected: Dict[str, int],
    ) -> None:
        # Préparer les launchers
        launchers = []
        for launcher_dict in config_map.get("launchers", []):
            if launcher_dict["type"] == "local":
                launchers.append(
                    LocalConfig.from_dict(
                        {
                            "id": launcher_dict["id"],
                            "type": "local",
                            "name": "name",
                            "enable_nb_cores_detection": False,
                            "nb_cores": launcher_dict.get("nb_cores", {}),
                        }
                    )
                )
            elif launcher_dict["type"] == "slurm":
                launchers.append(
                    SlurmConfig.from_dict(
                        {
                            "id": launcher_dict["id"],
                            "type": "slurm",
                            "name": "name",
                            "enable_nb_cores_detection": False,
                            "nb_cores": launcher_dict.get("nb_cores", {}),
                        }
                    )
                )

        # Créer la config complète
        launcher_config = LauncherConfig(default=config_map.get("default"), configs=launchers)
        config = Config(launcher=launcher_config)

        launcher_service = LauncherService(
            config=config,
            study_service=Mock(),
            output_service=Mock(),
            login_service=Mock(),
            job_result_repository=Mock(),
            factory_launcher=Mock(),
            event_bus=Mock(),
            file_transfer_manager=Mock(),
            task_service=Mock(),
            cache=Mock(),
        )

        # Exécution du test
        try:
            actual = launcher_service.get_nb_cores(solver)
        except ValueError as e:
            assert e.args[0] == f"'{solver}' is not a valid Launcher"
        else:
            assert actual == NbCoresConfig(**expected)

    @with_admin_user
    @pytest.mark.unit_test
    def test_service_kill_job(self, tmp_path: Path) -> None:
        study_service = Mock()
        study_service.get_study.return_value = Mock(spec=Study, groups=[], owner=None, public_mode=PublicMode.NONE)

        launcher_service = LauncherService(
            config=Config(storage=StorageConfig(tmp_dir=tmp_path)),
            study_service=study_service,
            output_service=OutputService(study_service, Mock(), Mock(), Mock(), Mock()),
            login_service=Mock(),
            job_result_repository=Mock(),
            event_bus=Mock(),
            factory_launcher=Mock(),
            file_transfer_manager=Mock(),
            task_service=Mock(),
            cache=Mock(),
        )
        launcher = "slurm"
        job_id = "job_id"
        job_result_mock = Mock()
        job_result_mock.id = job_id
        job_result_mock.study_id = "study_id"
        job_result_mock.launcher = launcher
        job_result_mock.owner_id = 36
        launcher_service.job_result_repository.get.return_value = job_result_mock
        launcher_service.launchers = {"slurm": Mock()}

        job_status = launcher_service.kill_job(job_id=job_id)

        launcher_service.launchers[launcher].kill_job.assert_called_once_with(job_id=job_id)

        assert job_status.job_status == JobStatus.FAILED
        launcher_service.job_result_repository.save.assert_called_once_with(job_status)

    def test_append_logs(self, tmp_path: Path) -> None:
        study_service = Mock()
        study_service.get_study.return_value = Mock(spec=Study, groups=[], owner=None, public_mode=PublicMode.NONE)

        launcher_service = LauncherService(
            config=Config(storage=StorageConfig(tmp_dir=tmp_path)),
            study_service=study_service,
            output_service=OutputService(study_service, Mock(), Mock(), Mock(), Mock()),
            login_service=Mock(),
            job_result_repository=Mock(),
            event_bus=Mock(),
            factory_launcher=Mock(),
            file_transfer_manager=Mock(),
            task_service=Mock(),
            cache=Mock(),
        )
        launcher = "slurm"
        job_id = "job_id"
        job_result_mock = Mock()
        job_result_mock.id = job_id
        job_result_mock.study_id = "study_id"
        job_result_mock.output_id = None
        job_result_mock.launcher = launcher
        job_result_mock.logs = []
        launcher_service.job_result_repository.get.return_value = job_result_mock

        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(engine)
        # noinspection SpellCheckingInspection
        DBSessionMiddleware(
            None,
            custom_engine=engine,
            session_args={"autocommit": False, "autoflush": False},
        )
        launcher_service.append_log(job_id, "test", JobLogType.BEFORE)
        launcher_service.job_result_repository.save.assert_called_with(job_result_mock)
        assert job_result_mock.logs[0].message == "test"
        assert job_result_mock.logs[0].job_id == "job_id"
        assert job_result_mock.logs[0].log_type == str(JobLogType.BEFORE)

    def test_get_logs(self, tmp_path: Path) -> None:
        study_service = Mock()
        launcher_service = LauncherService(
            config=Config(storage=StorageConfig(tmp_dir=tmp_path)),
            study_service=study_service,
            output_service=OutputService(study_service, Mock(), Mock(), Mock(), Mock()),
            login_service=Mock(),
            job_result_repository=Mock(),
            event_bus=Mock(),
            factory_launcher=Mock(),
            file_transfer_manager=Mock(),
            task_service=Mock(),
            cache=Mock(),
        )
        launcher = "slurm"
        job_id = "job_id"
        job_result_mock = Mock()
        job_result_mock.id = job_id
        job_result_mock.study_id = "study_id"
        job_result_mock.output_id = None
        job_result_mock.launcher = launcher
        job_result_mock.logs = [
            JobLog(message="first message", log_type=str(JobLogType.BEFORE)),
            JobLog(message="second message", log_type=str(JobLogType.BEFORE)),
            JobLog(message="last message", log_type=str(JobLogType.AFTER)),
        ]
        job_result_mock.launcher_params = '{"archive_output": false}'

        launcher_service.job_result_repository.get.return_value = job_result_mock
        slurm_launcher = Mock()
        launcher_service.launchers = {"slurm": slurm_launcher}
        slurm_launcher.get_log.return_value = "launcher logs"

        logs = launcher_service.get_log(job_id, LogType.STDOUT)
        assert logs == "first message\nsecond message\nlauncher logs\nlast message"
        logs = launcher_service.get_log(job_id, LogType.STDERR)
        assert logs == "launcher logs"

        study_service.get_logs.side_effect = ["some sim log", "error log"]

        job_result_mock.output_id = "some id"
        logs = launcher_service.get_log(job_id, LogType.STDOUT)
        assert logs == "first message\nsecond message\nsome sim log\nlast message"

        logs = launcher_service.get_log(job_id, LogType.STDERR)
        assert logs == "error log"

        study_service.get_logs.assert_has_calls(
            [
                call("study_id", "some id", job_id, False),
                call("study_id", "some id", job_id, True),
            ]
        )

    @with_admin_user
    def test_manage_output(self, tmp_path: Path) -> None:
        study_service = Mock()
        study_service.get_study.return_value = Mock(spec=Study, groups=[], owner=None, public_mode=PublicMode.NONE)
        output_service = Mock(spec=OutputService)
        output_service.import_output.return_value = ""

        launcher_service = LauncherService(
            config=Mock(storage=StorageConfig(tmp_dir=tmp_path)),
            study_service=study_service,
            output_service=output_service,
            login_service=Mock(),
            job_result_repository=Mock(),
            event_bus=Mock(),
            factory_launcher=Mock(),
            file_transfer_manager=Mock(),
            task_service=Mock(),
            cache=Mock(),
        )

        output_path = tmp_path / "output"
        zipped_output_path = tmp_path / "zipped_output"
        os.mkdir(output_path)
        os.mkdir(zipped_output_path)
        new_output_path = output_path / "new_output"
        os.mkdir(new_output_path)
        (new_output_path / "log").touch()
        (new_output_path / "data").touch()
        additional_log = tmp_path / "output.log"
        additional_log.write_text("some log")
        new_output_zipped_path = zipped_output_path / "test.zip"
        with ZipFile(new_output_zipped_path, "w", ZIP_DEFLATED) as output_data:
            output_data.writestr("some output", "0\n1")
        job_id = "job_id"
        zipped_job_id = "zipped_job_id"
        study_id = "study_id"
        launcher_service.job_result_repository.get.side_effect = [
            None,
            JobResult(id=job_id, study_id=study_id),
            JobResult(id=job_id, study_id=study_id, output_id="some id"),
            JobResult(id=zipped_job_id, study_id=study_id),
            JobResult(
                id=job_id,
                study_id=study_id,
            ),
            JobResult(
                id=job_id,
                study_id=study_id,
                launcher_params=json.dumps(
                    {
                        "archive_output": False,
                        f"{LAUNCHER_PARAM_NAME_SUFFIX}": "hello",
                    }
                ),
            ),
        ]
        with pytest.raises(JobNotFound):
            launcher_service._import_output(job_id, output_path, {"out.log": [additional_log]})

        launcher_service._import_output(job_id, output_path, {"out.log": [additional_log]})
        assert not launcher_service._get_job_output_fallback_path(job_id).exists()
        launcher_service.output_service.import_output.assert_called()

        launcher_service.download_output("job_id")
        launcher_service.output_service.export_output.assert_called()

        launcher_service._import_output(
            zipped_job_id,
            zipped_output_path,
            {
                "out.log": [additional_log],
                "antares-out": [additional_log],
                "antares-err": [additional_log],
            },
        )
        launcher_service.study_service.save_logs.has_calls(
            [
                call(study_id, zipped_job_id, "out.log", "some log"),
                call(study_id, zipped_job_id, "out", "some log"),
                call(study_id, zipped_job_id, "err", "some log"),
            ]
        )

        launcher_service.output_service.import_output.side_effect = [
            StudyNotFoundError(""),
            StudyNotFoundError(""),
        ]

        assert launcher_service._import_output(job_id, output_path, {"out.log": [additional_log]}) is None

        (new_output_path / "info.antares-output").write_text(
            f"[general]\nmode=Economy\nname=foo\ntimestamp={time.time()}"
        )
        output_name = launcher_service._import_output(job_id, output_path, {"out.log": [additional_log]})
        assert output_name is not None
        assert output_name.endswith("-hello")
        assert launcher_service._get_job_output_fallback_path(job_id).exists()
        assert (launcher_service._get_job_output_fallback_path(job_id) / output_name / "out.log").exists()

        launcher_service.job_result_repository.get.reset_mock()
        launcher_service.job_result_repository.get.side_effect = [
            None,
            JobResult(id=job_id, study_id=study_id, output_id=output_name),
        ]
        with pytest.raises(JobNotFound):
            launcher_service.download_output("job_id")

        study_service.get_study.reset_mock()
        study_service.get_study.side_effect = StudyNotFoundError("")

        export_file = FileDownloadDTO(id="a", name="a", filename="a", ready=True)
        launcher_service.file_transfer_manager.request_download.return_value = FileDownload(
            id="a", name="a", filename="a", ready=True, path="a"
        )
        launcher_service.task_service.add_task.return_value = "some id"

        assert launcher_service.download_output("job_id") == FileDownloadTaskDTO(task="some id", file=export_file)

        launcher_service.remove_job(job_id)
        assert not launcher_service._get_job_output_fallback_path(job_id).exists()

    def test_save_solver_stats(self, tmp_path: Path) -> None:
        study_service = Mock()
        study_service.get_study.return_value = Mock(spec=Study, groups=[], owner=None, public_mode=PublicMode.NONE)

        launcher_service = LauncherService(
            config=Mock(storage=StorageConfig(tmp_dir=tmp_path)),
            study_service=study_service,
            output_service=OutputService(study_service, Mock(), Mock(), Mock(), Mock()),
            login_service=Mock(),
            job_result_repository=Mock(),
            event_bus=Mock(),
            factory_launcher=Mock(),
            file_transfer_manager=Mock(),
            task_service=Mock(),
            cache=Mock(),
        )

        job_id = "job_id"
        study_id = "study_id"
        job_result = JobResult(
            id=job_id,
            study_id=study_id,
            job_status=JobStatus.SUCCESS,
            owner_id=1,
        )

        output_path = tmp_path / "some-output"
        output_path.mkdir()

        launcher_service._save_solver_stats(job_result, output_path)
        repository = launcher_service.job_result_repository
        repository.save.assert_not_called()

        expected_saved_stats = """#item	duration_ms	NbOccurences
        mc_years	216328	1
        study_loading	4304	1
        survey_report	158	1
        total	244581	1
        tsgen_hydro	1683	1
        tsgen_load	2702	1
        tsgen_solar	21606	1
        tsgen_thermal	407	2
        tsgen_wind	2500	1
            """
        (output_path / EXECUTION_INFO_FILE).write_text(expected_saved_stats)

        launcher_service._save_solver_stats(job_result, output_path)
        assert repository.save.call_count == 1

        # SQLAlchemy provides its own way to handle object comparison, which ensures
        # that the comparison is based on the database identity of the objects.
        # But, here, in that unit test, objects are not in a database session,
        # so we need to compare them manually.
        mock_call = repository.save.mock_calls[0]
        actual_obj: JobResult = mock_call.args[0]
        expected_obj = JobResult(
            id=job_id,
            study_id=study_id,
            job_status=JobStatus.SUCCESS,
            solver_stats=expected_saved_stats,
            owner_id=1,
        )
        assert actual_obj.to_dto().model_dump() == expected_obj.to_dto().model_dump()

        zip_file = tmp_path / "test.zip"
        with ZipFile(zip_file, "w", ZIP_DEFLATED) as output_data:
            output_data.writestr(EXECUTION_INFO_FILE, "0\n1")

        launcher_service._save_solver_stats(job_result, zip_file)
        assert repository.save.call_count == 2
        mock_call = repository.save.mock_calls[-1]
        actual_obj: JobResult = mock_call.args[0]
        expected_obj = JobResult(
            id=job_id,
            study_id=study_id,
            job_status=JobStatus.SUCCESS,
            solver_stats="0\n1",
            owner_id=1,
        )
        assert actual_obj.to_dto().model_dump() == expected_obj.to_dto().model_dump()

    @pytest.mark.parametrize(
        ["running_jobs", "expected_result", "default_launcher"],
        [
            pytest.param(
                [],
                {
                    "allocatedCpuRate": 0.0,
                    "clusterLoadRate": 0.0,
                    "nbQueuedJobs": 0,
                    "launcherStatus": "SUCCESS",
                },
                "local",
                id="local_no_running_job",
            ),
            pytest.param(
                [
                    Mock(
                        spec=JobResult,
                        launcher="local",
                        launcher_params=None,
                    ),
                    Mock(
                        spec=JobResult,
                        launcher="local",
                        launcher_params='{"nb_cpu": 7}',
                    ),
                ],
                {
                    "allocatedCpuRate": min(100.0, 800 / (os.cpu_count() or 1)),
                    "clusterLoadRate": min(100.0, 800 / (os.cpu_count() or 1)),
                    "nbQueuedJobs": 0,
                    "launcherStatus": "SUCCESS",
                },
                "local",
                id="local_with_running_jobs",
            ),
            pytest.param(
                [],
                {
                    "allocatedCpuRate": 0.0,
                    "clusterLoadRate": 0.0,
                    "nbQueuedJobs": 0,
                    "launcherStatus": "SUCCESS",
                },
                "slurm",
                id="slurm launcher with no config",
                marks=pytest.mark.xfail(
                    reason="Configuration is not available for the slurm launcher",
                    raises=InvalidConfigurationError,
                    strict=True,
                ),
            ),
        ],
    )
    def test_get_load(
        self,
        tmp_path: Path,
        running_jobs: List[JobResult],
        expected_result: Dict[str, Any],
        default_launcher: str,
    ) -> None:
        study_service = Mock()
        job_repository = Mock()

        config = Config(
            storage=StorageConfig(tmp_dir=tmp_path),
            launcher=LauncherConfig(default=default_launcher, configs=[LocalConfig(id="local", name="name")]),
        )

        launcher_mock = Mock()
        launcher_mock.get_load.return_value = LauncherLoadDTO.model_validate(expected_result)

        launchers_dict = {}
        if default_launcher == "local":
            launchers_dict[default_launcher] = launcher_mock

        factory_launcher_mock = Mock()
        factory_launcher_mock.build_launcher.return_value = launchers_dict

        launcher_service = LauncherService(
            config=config,
            study_service=study_service,
            output_service=OutputService(study_service, Mock(), Mock(), Mock(), Mock()),
            login_service=Mock(),
            job_result_repository=job_repository,
            event_bus=Mock(),
            factory_launcher=factory_launcher_mock,
            file_transfer_manager=Mock(),
            task_service=Mock(),
            cache=Mock(),
        )

        job_repository.get_running.return_value = running_jobs

        launcher_expected_result = LauncherLoadDTO.model_validate(expected_result)
        actual_result = launcher_service.get_load(default_launcher)

        assert launcher_expected_result.launcher_status == actual_result.launcher_status
        assert launcher_expected_result.nb_queued_jobs == actual_result.nb_queued_jobs
        assert math.isclose(
            launcher_expected_result.cluster_load_rate,
            actual_result.cluster_load_rate,
        )
        assert math.isclose(
            launcher_expected_result.allocated_cpu_rate,
            actual_result.allocated_cpu_rate,
        )

    def test_import_output_is_called_with_the_right_user(self, tmp_path: Path) -> None:
        # Create user
        jwt_user = JWTUser(id=2, impersonator=2, type="users")
        # Make the login service return this user
        login_service = Mock()
        login_service.get_jwt.return_value = jwt_user
        # Put this user as the job owner
        job_result = JobResult(study_id="study_id", owner_id=jwt_user.id)
        job_repository = Mock()
        job_repository.get.return_value = job_result

        # fake import_output function that checks the current user
        def fake_import_output(uuid: str, output: Path, output_name_suffix: None, auto_unzip: bool) -> None:
            assert get_current_user() == jwt_user

        output_service = Mock()
        output_service.import_output.side_effect = fake_import_output

        # Builds the service
        launcher_service = LauncherService(
            config=Mock(),
            study_service=Mock(),
            output_service=output_service,
            login_service=login_service,
            job_result_repository=job_repository,
            event_bus=Mock(),
            factory_launcher=Mock(),
            file_transfer_manager=Mock(),
            task_service=Mock(),
            cache=Mock(),
        )

        # Ensures the output_service.import_output method was called with the right user
        launcher_service._import_output("job_id", tmp_path, {})
