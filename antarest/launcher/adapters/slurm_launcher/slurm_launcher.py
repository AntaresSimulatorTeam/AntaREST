import argparse
import logging
import os
import shutil
import threading
import time
from copy import deepcopy
from pathlib import Path
from typing import Callable, Optional, Dict
from uuid import UUID, uuid4

from antareslauncher.data_repo.data_repo_tinydb import DataRepoTinydb
from antareslauncher.main import MainParameters, run_with
from antareslauncher.main_option_parser import (
    MainOptionParser,
    ParserParameters,
)
from antareslauncher.study_dto import StudyDTO
from antarest.core.config import Config, SlurmConfig
from antarest.core.interfaces.eventbus import (
    IEventBus,
    Event,
    EventType,
    EventChannelDirectory,
)
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.model import JSON
from antarest.core.requests import RequestParameters
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.launcher.adapters.abstractlauncher import (
    AbstractLauncher,
    LauncherInitException,
    LauncherCallbacks,
)
from antarest.launcher.adapters.log_manager import LogTailManager
from antarest.launcher.model import JobStatus, LogType
from antarest.study.service import StudyService

logger = logging.getLogger(__name__)
logging.getLogger("paramiko").setLevel("WARN")


class VersionNotSupportedError(Exception):
    pass


class JobIdNotFound(Exception):
    pass


class SlurmLauncher(AbstractLauncher):
    def __init__(
        self,
        config: Config,
        study_service: StudyService,
        callbacks: LauncherCallbacks,
        event_bus: IEventBus,
    ) -> None:
        super().__init__(config, study_service, callbacks)
        if config.launcher.slurm is None:
            raise LauncherInitException()

        self.slurm_config: SlurmConfig = config.launcher.slurm
        self.check_state: bool = True
        self.event_bus = event_bus
        self.thread: Optional[threading.Thread] = None
        self.job_id_to_study_id: Dict[str, str] = {}
        self._check_config()
        self.log_tail_manager = LogTailManager(
            self.slurm_config.local_workspace
        )
        self.launcher_args = self._init_launcher_arguments()
        self.launcher_params = self._init_launcher_parameters()
        self.data_repo_tinydb = DataRepoTinydb(
            database_file_path=(
                self.launcher_params.json_dir
                / self.launcher_params.default_json_db_name
            ),
            db_primary_key=self.launcher_params.db_primary_key,
        )

    def _check_config(self) -> None:
        assert (
            self.slurm_config.local_workspace.exists()
            and self.slurm_config.local_workspace.is_dir()
        )  # and check write permission

    def _loop(self) -> None:
        while self.check_state:
            self._check_studies_state()
            time.sleep(2)

    def start(self) -> None:
        self.check_state = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.check_state = False
        self.thread = None

    def _init_launcher_arguments(self) -> argparse.Namespace:
        main_options_parameters = ParserParameters(
            default_wait_time=self.slurm_config.default_wait_time,
            default_time_limit=self.slurm_config.default_time_limit,
            default_n_cpu=self.slurm_config.default_n_cpu,
            studies_in_dir=str(
                (Path(self.slurm_config.local_workspace) / "STUDIES_IN")
            ),
            log_dir=str((Path(self.slurm_config.local_workspace) / "LOGS")),
            finished_dir=str(
                (Path(self.slurm_config.local_workspace) / "OUTPUT")
            ),
            ssh_config_file_is_required=False,
            ssh_configfile_path_alternate1=None,
            ssh_configfile_path_alternate2=None,
        )

        parser: MainOptionParser = MainOptionParser(main_options_parameters)
        parser.add_basic_arguments()
        parser.add_advanced_arguments()
        arguments = parser.parse_args([])

        arguments.wait_mode = False
        arguments.check_queue = False
        arguments.json_ssh_config = None
        arguments.job_id_to_kill = None
        arguments.xpansion_mode = False
        arguments.version = False
        arguments.post_processing = False
        return arguments

    def _init_launcher_parameters(self) -> MainParameters:
        main_parameters = MainParameters(
            json_dir=self.slurm_config.local_workspace,
            default_json_db_name=self.slurm_config.default_json_db_name,
            slurm_script_path=self.slurm_config.slurm_script_path,
            antares_versions_on_remote_server=self.slurm_config.antares_versions_on_remote_server,
            default_ssh_dict={
                "username": self.slurm_config.username,
                "hostname": self.slurm_config.hostname,
                "port": self.slurm_config.port,
                "private_key_file": self.slurm_config.private_key_file,
                "key_password": self.slurm_config.key_password,
                "password": self.slurm_config.password,
            },
            db_primary_key="name",
        )
        return main_parameters

    def _delete_study(self, study_path: Path) -> None:
        if (
            self.slurm_config.local_workspace.absolute()
            in study_path.absolute().parents
        ):
            if study_path.exists():
                shutil.rmtree(study_path)

    def _import_study_output(
        self, job_id: str, xpansion_mode: bool = False
    ) -> Optional[str]:
        study_id = self.job_id_to_study_id[job_id]
        if xpansion_mode:
            study_id = (
                self.storage_service.variant_study_service.create_variant_study(
                    study_id,
                    "xpansion result",
                    params=RequestParameters(user=DEFAULT_ADMIN_USER),
                )
                or study_id
            )

        return self.storage_service.import_output(
            study_id,
            self.slurm_config.local_workspace / "OUTPUT" / job_id / "output",
            params=RequestParameters(DEFAULT_ADMIN_USER),
        )

    def _check_studies_state(self) -> None:
        try:
            run_with(
                arguments=self.launcher_args,
                parameters=self.launcher_params,
                show_banner=False,
            )
        except Exception as e:
            logger.info("Could not get data on remote server", exc_info=e)

        study_list = self.data_repo_tinydb.get_list_of_studies()

        all_done = True

        for study in study_list:
            if study.name not in self.job_id_to_study_id:
                # this job is handled by another worker process
                continue

            all_done = all_done and (study.finished or study.with_error)
            if study.done:
                try:
                    self.log_tail_manager.stop_tracking(
                        SlurmLauncher._get_log_path(study)
                    )
                    with db():
                        output_id: Optional[str] = None
                        if not study.with_error:
                            output_id = self._import_study_output(study.name)
                        self.callbacks.update_status(
                            study.name,
                            JobStatus.FAILED
                            if study.with_error or output_id is None
                            else JobStatus.SUCCESS,
                            None,
                            output_id,
                        )
                except Exception as e:
                    logger.error(
                        f"Failed to finalize study {study.name} launch",
                        exc_info=e,
                    )
                finally:
                    self._clean_up_study(study.name)
            else:
                self.log_tail_manager.track(
                    SlurmLauncher._get_log_path(study),
                    self.create_update_log(
                        study.name, self.job_id_to_study_id[study.name]
                    ),
                )

        if all_done:
            self.stop()

    def create_update_log(
        self, job_id: str, study_id: str
    ) -> Callable[[str], None]:
        def update_log(log_line: str) -> None:
            self.event_bus.push(
                Event(
                    type=EventType.STUDY_JOB_LOG_UPDATE,
                    payload={
                        "log": log_line,
                        "job_id": job_id,
                        "study_id": study_id,
                    },
                    channel=EventChannelDirectory.JOB_LOGS + job_id,
                )
            )

        return update_log

    @staticmethod
    def _get_log_path(
        study: StudyDTO, log_type: LogType = LogType.STDOUT
    ) -> Optional[Path]:
        log_dir = Path(study.job_log_dir)
        log_prefix = (
            "antares-out-" if log_type == LogType.STDOUT else "antares-err-"
        )
        if log_dir.exists() and log_dir.is_dir():
            for fname in os.listdir(log_dir):
                if fname.startswith(log_prefix):
                    return log_dir / fname
        return None

    def _clean_local_workspace(self) -> None:
        logger.info("Cleaning up slurm workspace")
        local_workspace = self.slurm_config.local_workspace
        for filename in os.listdir(local_workspace):
            file_path = os.path.join(local_workspace, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)

    def _assert_study_version_is_supported(
        self, study_uuid: str, params: RequestParameters
    ) -> None:
        study_version = self.storage_service.get_study_information(
            study_uuid, params=params
        ).version
        if (
            str(study_version)
            not in self.slurm_config.antares_versions_on_remote_server
        ):
            raise VersionNotSupportedError(
                f"Study version ({study_version}) is not supported. Currently supported versions are"
                f" {', '.join(self.slurm_config.antares_versions_on_remote_server)}"
            )

    def _clean_up_study(self, launch_id: str) -> None:
        self.data_repo_tinydb.remove_study(launch_id)
        self._delete_study(
            self.slurm_config.local_workspace / "OUTPUT" / launch_id
        )
        del self.job_id_to_study_id[launch_id]

    def _run_study(
        self,
        study_uuid: str,
        launch_uuid: str,
        launcher_params: Optional[JSON],
        params: RequestParameters,
    ) -> None:
        with db():
            study_path = Path(self.launcher_args.studies_in) / str(launch_uuid)

            self.job_id_to_study_id[str(launch_uuid)] = study_uuid

            if not self.thread:
                self._clean_local_workspace()

            try:
                # export study
                self.storage_service.export_study_flat(
                    study_uuid, params, study_path, outputs=False
                )

                self._assert_study_version_is_supported(study_uuid, params)

                launcher_args = self._check_and_apply_launcher_params(
                    launcher_params
                )
                run_with(
                    launcher_args, self.launcher_params, show_banner=False
                )
                self.callbacks.update_status(
                    str(launch_uuid), JobStatus.RUNNING, None, None
                )
            except Exception as e:
                logger.error(
                    f"Failed to launch study {study_uuid}", exc_info=e
                )
                self.callbacks.update_status(
                    str(launch_uuid), JobStatus.FAILED, str(e), None
                )
                self._delete_study(study_path)
                self._clean_up_study(str(launch_uuid))

            if not self.thread:
                self.start()

            self._delete_study(study_path)

    def _check_and_apply_launcher_params(
        self, launcher_params: Optional[JSON]
    ) -> argparse.Namespace:
        if launcher_params:
            launcher_args = deepcopy(self.launcher_args)
            if launcher_params.get("xpansion", False):
                launcher_args.xpansion_mode = True
            time_limit = launcher_params.get("time_limit", None)
            if time_limit and isinstance(time_limit, int):
                if 3600 < time_limit < 604800:
                    launcher_args.time_limit = time_limit
                else:
                    logger.warning(
                        f"Invalid slurm launcher time limit ({time_limit}), should be between 3600 and 604800"
                    )
            post_processing = launcher_params.get("post_processing", False)
            if isinstance(post_processing, bool):
                launcher_args.post_processing = post_processing
            nb_cpu = launcher_params.get("nb_cpu", 12)
            if isinstance(nb_cpu, int):
                if 0 < nb_cpu <= 24:
                    launcher_args.n_cpu = nb_cpu
                else:
                    logger.warning(
                        f"Invalid slurm launcher nb_cpu ({nb_cpu}), should be between 1 and 24"
                    )
            return launcher_args
        return self.launcher_args

    def run_study(
        self,
        study_uuid: str,
        version: str,
        launcher_parameters: Optional[JSON],
        params: RequestParameters,
    ) -> UUID:  # TODO: version ?
        launch_uuid = uuid4()

        thread = threading.Thread(
            target=self._run_study,
            args=(study_uuid, launch_uuid, launcher_parameters, params),
        )
        thread.start()

        return launch_uuid

    def get_log(self, job_id: str, log_type: LogType) -> Optional[str]:
        for study in self.data_repo_tinydb.get_list_of_studies():
            if study.name == job_id:
                log_path = SlurmLauncher._get_log_path(study, log_type)
                if log_path:
                    return log_path.read_text()
        return None

    def kill_job(self, job_id: str) -> None:
        launcher_args = deepcopy(self.launcher_args)
        for study in self.data_repo_tinydb.get_list_of_studies():
            if study.name == job_id:
                launcher_args.job_id_to_kill = study.job_id
                run_with(
                    launcher_args, self.launcher_params, show_banner=False
                )
                return

        raise JobIdNotFound()
