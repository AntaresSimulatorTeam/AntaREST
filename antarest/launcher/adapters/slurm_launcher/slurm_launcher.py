import argparse
import logging
import os
import re
import shutil
import tempfile
import threading
import time
from copy import deepcopy
from pathlib import Path
from typing import Callable, Optional, Dict, Awaitable, List

from filelock import FileLock

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
)
from antarest.core.model import JSON
from antarest.core.requests import RequestParameters
from antarest.core.utils.utils import assert_this
from antarest.launcher.adapters.abstractlauncher import (
    AbstractLauncher,
    LauncherInitException,
    LauncherCallbacks,
)
from antarest.launcher.adapters.log_manager import LogTailManager
from antarest.launcher.adapters.slurm_launcher.batch_job import BatchJobManager
from antarest.launcher.model import JobStatus, LogType
from antarest.study.storage.rawstudy.model.filesystem.factory import (
    StudyFactory,
    FileStudy,
)

logger = logging.getLogger(__name__)
logging.getLogger("paramiko").setLevel("WARN")

MAX_NB_CPU = 24
MAX_TIME_LIMIT = 864000
MIN_TIME_LIMIT = 3600
WORKSPACE_LOCK_FILE_NAME = ".lock"
LOCK_FILE_NAME = "slurm_launcher_init.lock"
LOG_DIR_NAME = "LOGS"
STUDIES_INPUT_DIR_NAME = "STUDIES_IN"
STUDIES_OUTPUT_DIR_NAME = "OUTPUT"


class VersionNotSupportedError(Exception):
    pass


class JobIdNotFound(Exception):
    pass


class SlurmLauncher(AbstractLauncher):
    def __init__(
        self,
        config: Config,
        callbacks: LauncherCallbacks,
        event_bus: IEventBus,
        study_factory: StudyFactory,
        use_private_workspace: bool = True,
        retrieve_existing_jobs: bool = False,
    ) -> None:
        super().__init__(config, callbacks, event_bus)
        if config.launcher.slurm is None:
            raise LauncherInitException()

        self.study_factory = study_factory
        self.slurm_config: SlurmConfig = config.launcher.slurm
        self.check_state: bool = True
        self.event_bus = event_bus
        self.event_bus.add_listener(
            self._create_event_listener(), [EventType.STUDY_JOB_CANCEL_REQUEST]
        )
        self.thread: Optional[threading.Thread] = None
        self.batch_sub_jobs: Dict[str, str] = {}
        self._check_config()
        self.antares_launcher_lock = threading.Lock()
        with FileLock(LOCK_FILE_NAME):
            self.local_workspace = self._init_workspace(use_private_workspace)

        self.batch_jobs = BatchJobManager(
            self.local_workspace.name, self.study_factory, config
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
        if retrieve_existing_jobs:
            self._retrieve_running_jobs()

    def _check_config(self) -> None:
        assert_this(
            self.slurm_config.local_workspace.exists()
            and self.slurm_config.local_workspace.is_dir()
        )  # and check write permission

    def _init_workspace(self, use_private_workspace: bool) -> Path:
        if use_private_workspace:
            for (
                existing_workspace
            ) in self.slurm_config.local_workspace.iterdir():
                lock_file = existing_workspace / WORKSPACE_LOCK_FILE_NAME
                if (
                    existing_workspace.is_dir()
                    and existing_workspace
                    != self.slurm_config.local_workspace / LOG_DIR_NAME
                    and not lock_file.exists()
                ):
                    logger.info(
                        f"Initiating slurm workspace into existing directory {existing_workspace}"
                    )
                    lock_file.touch()
                    return existing_workspace
            new_workspace = Path(
                tempfile.mkdtemp(dir=str(self.slurm_config.local_workspace))
            )
            lock_file = new_workspace / WORKSPACE_LOCK_FILE_NAME
            lock_file.touch()
            logger.info(
                f"Initiating slurm workspace in new directory {new_workspace}"
            )
            return new_workspace
        else:
            return Path(self.slurm_config.local_workspace)

    def _retrieve_running_jobs(self) -> None:
        self.batch_jobs.refresh_cache()
        if len(self.data_repo_tinydb.get_list_of_studies()) > 0:
            logger.info("Old job retrieved, starting loop")
            self.start()

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
                    / STUDIES_INPUT_DIR_NAME
                )
            ),
            log_dir=str(
                (Path(self.slurm_config.local_workspace) / LOG_DIR_NAME)
            ),
            finished_dir=str(
                (
                    Path(local_workspace or self.slurm_config.local_workspace)
                    / STUDIES_OUTPUT_DIR_NAME
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

    def _delete_workspace_file(self, study_path: Path) -> None:
        logger.info(f"Deleting workspace file at {study_path}")
        if self.local_workspace.absolute() in study_path.absolute().parents:
            if study_path.exists():
                if study_path.is_dir():
                    shutil.rmtree(study_path)
                else:
                    os.unlink(study_path)

    def _import_study_output(
        self,
        job_id: str,
        launcher_studies: List[StudyDTO],
    ) -> Optional[str]:

        if (
            len(launcher_studies) == 1
            and launcher_studies[0].xpansion_mode is not None
        ):
            self._import_xpansion_result(
                job_id, launcher_studies[0].xpansion_mode
            )

        output_dir = self.batch_jobs.merge_outputs(
            job_id,
            launcher_studies,
            self.local_workspace / STUDIES_OUTPUT_DIR_NAME,
        )

        launcher_logs: Dict[str, List[Path]] = {
            "antares-out.log": [],
            "antares-err.log": [],
        }
        for study in launcher_studies:
            log_dir = study.job_log_dir
            if log_dir is not None:
                out_log = SlurmLauncher._get_log_path_from_log_dir(
                    Path(log_dir), LogType.STDOUT
                )
                if out_log:
                    launcher_logs["antares-out.log"].append(out_log)
                err_log = SlurmLauncher._get_log_path_from_log_dir(
                    Path(log_dir), LogType.STDERR
                )
                if err_log:
                    launcher_logs["antares-err.log"].append(err_log)

        return (
            self.callbacks.import_output(
                job_id,
                output_dir,
                launcher_logs,
            )
            if output_dir
            else None
        )

    def _import_xpansion_result(self, job_id: str, xpansion_mode: str) -> None:
        output_path = (
            self.local_workspace / STUDIES_OUTPUT_DIR_NAME / job_id / "output"
        )
        if output_path.exists() and len(os.listdir(output_path)) == 1:
            output_path = output_path / os.listdir(output_path)[0]
            shutil.copytree(
                self.local_workspace
                / STUDIES_OUTPUT_DIR_NAME
                / job_id
                / "input"
                / "links",
                output_path / "updated_links",
            )
            if xpansion_mode == "r":
                shutil.copytree(
                    self.local_workspace
                    / STUDIES_OUTPUT_DIR_NAME
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

        # fetch all study states and group them by batch job
        batch_jobs: Dict[str, List[StudyDTO]] = {}
        for study in study_list:
            all_done = all_done and (study.finished or study.with_error)
            if study.done:
                self.log_tail_manager.stop_tracking(
                    SlurmLauncher._get_log_path(study)
                )
                parent_job = self.batch_jobs.get_batch_job_parent(study.name)
                if parent_job:
                    if parent_job not in batch_jobs:
                        batch_jobs[parent_job] = []
                    batch_jobs[parent_job].append(study)
                    continue
            elif not self.log_tail_manager.is_tracking(
                SlurmLauncher._get_log_path(study)
            ):
                parent_job = self.batch_jobs.get_batch_job_parent(study.name)
                if parent_job:
                    self.log_tail_manager.track(
                        SlurmLauncher._get_log_path(study),
                        self.create_update_log(parent_job),
                    )

        # for each batch job, check if all batch is done and then run the import of all results
        for batch_job in batch_jobs:
            if len(batch_jobs[batch_job]) == len(
                self.batch_jobs.get_batch_job_children(batch_job)
            ):
                try:
                    output_id: Optional[str] = None
                    try:
                        output_id = self._import_study_output(
                            batch_job, batch_jobs[batch_job]
                        )
                    finally:
                        self.callbacks.update_status(
                            batch_job,
                            JobStatus.FAILED
                            if output_id is None
                            else JobStatus.SUCCESS,
                            None,
                            output_id,
                        )
                except Exception as e:
                    logger.error(
                        f"Failed to finalize study {batch_job} launch",
                        exc_info=e,
                    )
                finally:
                    self._clean_up_study(batch_job, is_parent=True)

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

    def _assert_study_version_is_supported(self, study_version: str) -> None:
        if (
            str(study_version)
            not in self.slurm_config.antares_versions_on_remote_server
        ):
            raise VersionNotSupportedError(
                f"Study version ({study_version}) is not supported. Currently supported versions are"
                f" {', '.join(self.slurm_config.antares_versions_on_remote_server)}"
            )

    def _clean_up_study(self, launch_id: str, is_parent: bool = False) -> None:
        logger.info(f"Cleaning up study with launch_id {launch_id}")
        if is_parent:
            children = self.batch_jobs.get_batch_job_children(launch_id)
            for child_id in children:
                self._clean_up_study(child_id, is_parent=False)
            self.batch_jobs.remove_batch_job(launch_id)
        else:
            self.data_repo_tinydb.remove_study(launch_id)

            self._delete_workspace_file(
                self.local_workspace / STUDIES_OUTPUT_DIR_NAME / launch_id
            )
            self._delete_workspace_file(
                self.local_workspace / STUDIES_INPUT_DIR_NAME / launch_id
            )
            if (self.local_workspace / STUDIES_OUTPUT_DIR_NAME).exists():
                for finished_zip in (
                    self.local_workspace / STUDIES_OUTPUT_DIR_NAME
                ).iterdir():
                    if finished_zip.is_file() and re.match(
                        f"finished_{launch_id}_\\d+", finished_zip.name
                    ):
                        self._delete_workspace_file(finished_zip)

    def _run_study(
        self,
        study_uuid: str,
        launch_uuid: str,
        launcher_params: Optional[JSON],
        version: str,
    ) -> None:
        # the default path and batch id for a launche
        study_path = Path(self.launcher_args.studies_in) / launch_uuid
        sub_job_ids = [launch_uuid]

        try:
            self._assert_study_version_is_supported(version)

            with self.antares_launcher_lock:
                # export study
                self.callbacks.export_study(
                    launch_uuid, study_uuid, study_path, launcher_params
                )

                # batch mode (export studies split in different folders with special playlist set)
                # if there is a need for multiple batch,
                # the first study export is moved to a new folder and other batch are copied from this export
                # this generate new sub ids for each batch
                sub_job_ids = self.batch_jobs.prepare_batch_study(
                    launch_uuid,
                    study_path,
                    Path(self.launcher_args.studies_in),
                )

                launcher_args = self._check_and_apply_launcher_params(
                    launcher_params
                )
                self.callbacks.append_before_log(
                    launch_uuid, f"Submitting study to slurm launcher"
                )
                run_with(
                    launcher_args, self.launcher_params, show_banner=False
                )
                self.callbacks.append_before_log(
                    launch_uuid, f"Study submitted"
                )
                logger.info("Study exported and run with launcher")

            self.callbacks.update_status(
                launch_uuid, JobStatus.RUNNING, None, None
            )
        except Exception as e:
            logger.error(f"Failed to launch study {study_uuid}", exc_info=e)
            self.callbacks.append_after_log(
                launch_uuid,
                f"Unexpected error when launching study : {str(e)}",
            )
            self.callbacks.update_status(
                launch_uuid, JobStatus.FAILED, str(e), None
            )
            self._clean_up_study(launch_uuid, is_parent=True)

        if not self.thread:
            self.start()

        # clean up study export after they are 'sent to the internet'
        for sub_job in sub_job_ids:
            self._delete_workspace_file(
                Path(self.launcher_args.studies_in) / sub_job
            )

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
                if MIN_TIME_LIMIT > time_limit:
                    logger.warning(
                        f"Invalid slurm launcher time limit ({time_limit}), should be higher than {MIN_TIME_LIMIT}. Using min limit."
                    )
                    launcher_args.time_limit = MIN_TIME_LIMIT
                elif time_limit >= MAX_TIME_LIMIT:
                    logger.warning(
                        f"Invalid slurm launcher time limit ({time_limit}), should be lower than {MAX_TIME_LIMIT}. Using max limit."
                    )
                    launcher_args.time_limit = MAX_TIME_LIMIT - 3600
                else:
                    launcher_args.time_limit = time_limit
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
        job_id: str,
        version: str,
        launcher_parameters: Optional[JSON],
        params: RequestParameters,
    ) -> None:

        thread = threading.Thread(
            target=self._run_study,
            args=(study_uuid, job_id, launcher_parameters, version),
        )
        thread.start()

    def get_log(self, job_id: str, log_type: LogType) -> Optional[str]:
        children = self.batch_jobs.get_batch_job_children(job_id)
        logs = []
        for child in children:
            log_path: Optional[Path] = None
            for study in self.data_repo_tinydb.get_list_of_studies():
                if study.name == child:
                    log_path = SlurmLauncher._get_log_path(study, log_type)
                    if log_path:
                        logs.append(log_path.read_text())
            # when this is not the current worker handling this job (found in data_repo_tinydb)
            log_dir = SlurmLauncher._find_log_dir(
                Path(self.launcher_args.log_dir) / "JOB_LOGS", child
            )
            if log_dir:
                log_path = SlurmLauncher._get_log_path_from_log_dir(
                    log_dir, log_type
                )
            if log_path:
                logs.append(log_path.read_text())
        if len(logs):
            return "\n----\n".join(logs)
        return None

    def _create_event_listener(self) -> Callable[[Event], Awaitable[None]]:
        async def _listen_to_kill_job(event: Event) -> None:
            if event.type == EventType.STUDY_JOB_CANCEL_REQUEST:
                self.kill_job(event.payload, dispatch=False)

        return _listen_to_kill_job

    def kill_job(self, job_id: str, dispatch: bool = True) -> None:
        launcher_args = deepcopy(self.launcher_args)
        jobs = self.batch_jobs.get_batch_job_children(job_id)
        for job in jobs:
            found = False
            for study in self.data_repo_tinydb.get_list_of_studies():
                if study.name == job:
                    launcher_args.job_id_to_kill = study.job_id
                    logger.info(
                        f"Cancelling job {job} (dispatched={not dispatch})"
                    )
                    with self.antares_launcher_lock:
                        run_with(
                            launcher_args,
                            self.launcher_params,
                            show_banner=False,
                        )
                    found = True
                    break
            if not found and dispatch:
                self.event_bus.push(
                    Event(
                        type=EventType.STUDY_JOB_CANCEL_REQUEST, payload=job_id
                    )
                )
                self.callbacks.update_status(
                    job_id,
                    JobStatus.FAILED,
                    None,
                    None,
                )
