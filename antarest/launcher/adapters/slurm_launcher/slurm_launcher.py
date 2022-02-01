import argparse
import logging
import os
import shutil
import tempfile
import threading
import time
from copy import deepcopy
from pathlib import Path
from typing import Callable, Optional, Dict, Awaitable
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

MAX_NB_CPU = 24
MAX_TIME_LIMIT = 604800
MIN_TIME_LIMIT = 3600


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
        use_private_workspace: bool = True,
    ) -> None:
        super().__init__(config, study_service, callbacks, event_bus)
        if config.launcher.slurm is None:
            raise LauncherInitException()

        self.slurm_config: SlurmConfig = config.launcher.slurm
        self.check_state: bool = True
        self.event_bus = event_bus
        self.event_bus.add_listener(
            self._create_event_listener(), [EventType.STUDY_JOB_CANCEL_REQUEST]
        )
        self.thread: Optional[threading.Thread] = None
        self.job_id_to_study_id: Dict[str, str] = {}
        self._check_config()
        self.antares_launcher_lock = threading.Lock()
        self.local_workspace = (
            Path(tempfile.mkdtemp(dir=str(self.slurm_config.local_workspace)))
            if use_private_workspace
            else Path(self.slurm_config.local_workspace)
        )

        self.log_tail_manager = LogTailManager(
            Path(self.slurm_config.local_workspace)
        )
        self.launcher_args = self._init_launcher_arguments(
            self.local_workspace
        )
        self.launcher_params = self._init_launcher_parameters(
            self.local_workspace
        )
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

    def _init_launcher_arguments(
        self, local_workspace: Optional[Path] = None
    ) -> argparse.Namespace:
        main_options_parameters = ParserParameters(
            default_wait_time=self.slurm_config.default_wait_time,
            default_time_limit=self.slurm_config.default_time_limit,
            default_n_cpu=self.slurm_config.default_n_cpu,
            studies_in_dir=str(
                (
                    Path(local_workspace or self.slurm_config.local_workspace)
                    / "STUDIES_IN"
                )
            ),
            log_dir=str((Path(self.slurm_config.local_workspace) / "LOGS")),
            finished_dir=str(
                (
                    Path(local_workspace or self.slurm_config.local_workspace)
                    / "OUTPUT"
                )
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
        arguments.xpansion_mode = None
        arguments.version = False
        arguments.post_processing = False
        return arguments

    def _init_launcher_parameters(
        self, local_workspace: Optional[Path] = None
    ) -> MainParameters:
        main_parameters = MainParameters(
            json_dir=local_workspace or self.slurm_config.local_workspace,
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
        logger.info(f"Deleting study export at {study_path}")
        if self.local_workspace.absolute() in study_path.absolute().parents:
            if study_path.exists():
                shutil.rmtree(study_path)

    def _import_study_output(
        self,
        job_id: str,
        xpansion_mode: Optional[str] = None,
        log_dir: Optional[str] = None,
    ) -> Optional[str]:
        study_id = self.job_id_to_study_id[job_id]
        if xpansion_mode is not None:
            self._import_xpansion_result(job_id, xpansion_mode)
        return self.storage_service.import_output(
            study_id,
            self.local_workspace / "OUTPUT" / job_id / "output",
            params=RequestParameters(DEFAULT_ADMIN_USER),
            log_path=SlurmLauncher._get_log_path_from_log_dir(
                Path(log_dir), LogType.STDOUT
            )
            if log_dir is not None
            else None,
        )

    def _import_xpansion_result(self, job_id: str, xpansion_mode: str) -> None:
        output_path = self.local_workspace / "OUTPUT" / job_id / "output"
        if output_path.exists() and len(os.listdir(output_path)) == 1:
            output_path = output_path / os.listdir(output_path)[0]
            shutil.copytree(
                self.local_workspace / "OUTPUT" / job_id / "input" / "links",
                output_path / "updated_links",
            )
            if xpansion_mode == "r":
                shutil.copytree(
                    self.local_workspace
                    / "OUTPUT"
                    / job_id
                    / "user"
                    / "expansion",
                    output_path / "results",
                )
        else:
            logger.warning("Output path in xpansion result not found")

    def _check_studies_state(self) -> None:
        try:
            with self.antares_launcher_lock:
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
                            output_id = self._import_study_output(
                                study.name,
                                study.xpansion_mode,
                                study.job_log_dir,
                            )
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

    @staticmethod
    def _get_log_path(
        study: StudyDTO, log_type: LogType = LogType.STDOUT
    ) -> Optional[Path]:
        log_dir = Path(study.job_log_dir)
        return SlurmLauncher._get_log_path_from_log_dir(log_dir, log_type)

    @staticmethod
    def _find_log_dir(base_log_dir: Path, job_id: str) -> Optional[Path]:
        if base_log_dir.exists() and base_log_dir.is_dir():
            for fname in os.listdir(base_log_dir):
                if fname.startswith(job_id):
                    return base_log_dir / fname
        return None

    @staticmethod
    def _get_log_path_from_log_dir(
        log_dir: Path, log_type: LogType = LogType.STDOUT
    ) -> Optional[Path]:
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
        local_workspace = self.local_workspace
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
        logger.info(f"Cleaning up study with launch_id {launch_id}")
        self.data_repo_tinydb.remove_study(launch_id)
        self._delete_study(self.local_workspace / "OUTPUT" / launch_id)
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

            try:
                # export study
                with self.antares_launcher_lock:
                    self.storage_service.export_study_flat(
                        study_uuid, params, study_path, outputs=False
                    )
                    self.callbacks.after_export_flat(
                        launch_uuid, study_uuid, study_path, launcher_params
                    )

                    self._assert_study_version_is_supported(study_uuid, params)

                    launcher_args = self._check_and_apply_launcher_params(
                        launcher_params
                    )
                    run_with(
                        launcher_args, self.launcher_params, show_banner=False
                    )
                    logger.info("Study exported and run with launcher")

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
                launcher_args.xpansion_mode = (
                    "r"
                    if launcher_params.get("xpansion_r_version", False)
                    else "cpp"
                )
            time_limit = launcher_params.get("time_limit", None)
            if time_limit and isinstance(time_limit, int):
                if MIN_TIME_LIMIT < time_limit < MAX_TIME_LIMIT:
                    launcher_args.time_limit = time_limit
                else:
                    logger.warning(
                        f"Invalid slurm launcher time limit ({time_limit}), should be between {MIN_TIME_LIMIT} and {MAX_TIME_LIMIT}"
                    )
            post_processing = launcher_params.get("post_processing", False)
            if isinstance(post_processing, bool):
                launcher_args.post_processing = post_processing
            nb_cpu = launcher_params.get("nb_cpu", None)
            if nb_cpu and isinstance(nb_cpu, int):
                if 0 < nb_cpu <= MAX_NB_CPU:
                    launcher_args.n_cpu = nb_cpu
                else:
                    logger.warning(
                        f"Invalid slurm launcher nb_cpu ({nb_cpu}), should be between 1 and 24"
                    )
            if (
                launcher_params.get("adequacy_patch", None) is not None
            ):  # the adequacy patch can be an empty object
                launcher_args.post_processing = True
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
        log_path: Optional[Path] = None
        for study in self.data_repo_tinydb.get_list_of_studies():
            if study.name == job_id:
                log_path = SlurmLauncher._get_log_path(study, log_type)
                if log_path:
                    return log_path.read_text()
        # when this is not the current worker handling this job (found in data_repo_tinydb)
        log_dir = SlurmLauncher._find_log_dir(
            Path(self.launcher_args.log_dir) / "JOB_LOGS", job_id
        )
        if log_dir:
            log_path = SlurmLauncher._get_log_path_from_log_dir(
                log_dir, log_type
            )
        if log_path:
            return log_path.read_text()
        return None

    def _create_event_listener(self) -> Callable[[Event], Awaitable[None]]:
        async def _listen_to_kill_job(event: Event) -> None:
            if event.type == EventType.STUDY_JOB_CANCEL_REQUEST:
                self.kill_job(event.payload, dispatch=False)

        return _listen_to_kill_job

    def kill_job(self, job_id: str, dispatch: bool = True) -> None:
        launcher_args = deepcopy(self.launcher_args)
        for study in self.data_repo_tinydb.get_list_of_studies():
            if study.name == job_id:
                launcher_args.job_id_to_kill = study.job_id
                logger.info(
                    f"Cancelling job {job_id} (dispatched={not dispatch})"
                )
                with self.antares_launcher_lock:
                    run_with(
                        launcher_args, self.launcher_params, show_banner=False
                    )
                return
        if dispatch:
            self.event_bus.push(
                Event(type=EventType.STUDY_JOB_CANCEL_REQUEST, payload=job_id)
            )
            self.callbacks.update_status(
                job_id,
                JobStatus.FAILED,
                None,
                None,
            )
