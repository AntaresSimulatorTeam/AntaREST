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

import argparse
import logging
import os
import re
import shutil
import tempfile
import threading
import time
import traceback
from pathlib import Path
from typing import Awaitable, Callable, Dict, List, Optional, cast

from antares.study.version import SolverVersion
from antareslauncher.data_repo.data_repo_tinydb import DataRepoTinydb
from antareslauncher.main import MainParameters, run_with
from antareslauncher.main_option_parser import MainOptionParser, ParserParameters
from antareslauncher.study_dto import StudyDTO
from filelock import FileLock
from typing_extensions import override

from antarest.core.config import NbCoresConfig, SlurmConfig, TimeLimitConfig
from antarest.core.interfaces.cache import ICache
from antarest.core.interfaces.eventbus import Event, EventType, IEventBus
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.model import PermissionInfo, PublicMode
from antarest.core.serde.ini_reader import read_ini
from antarest.core.serde.ini_writer import write_ini_file
from antarest.core.utils.archives import unzip
from antarest.core.utils.utils import assert_this
from antarest.launcher.adapters.abstractlauncher import AbstractLauncher, LauncherCallbacks
from antarest.launcher.adapters.log_manager import LogTailManager
from antarest.launcher.model import JobStatus, LauncherParametersDTO, LogType, XpansionParametersDTO
from antarest.login.utils import current_user_context

logger = logging.getLogger(__name__)
logging.getLogger("paramiko").setLevel("WARN")

WORKSPACE_LOCK_FILE_NAME = ".lock"
LOCK_FILE_NAME = "slurm_launcher_init.lock"
LOG_DIR_NAME = "LOGS"
STUDIES_INPUT_DIR_NAME = "STUDIES_IN"
STUDIES_OUTPUT_DIR_NAME = "OUTPUT"


class VersionNotSupportedError(Exception):
    pass


class JobIdNotFound(Exception):
    pass


class LauncherArgs(argparse.Namespace):
    """
    Launcher arguments to be passed to `antareslauncher.main.run_with`.
    """

    def __init__(self, launcher_args: argparse.Namespace):
        """
        Create a copy of the `argparse.Namespace` object.

        Args:
            launcher_args: The arguments to copy.
        """
        super().__init__()

        # known arguments
        self.other_options: Optional[str] = None
        self.xpansion_mode: Optional[str] = None
        self.time_limit: int = 0
        self.n_cpu: int = 0
        self.post_processing: bool = False

        args = vars(launcher_args)
        for key, value in args.items():
            setattr(self, key, value)

    def _append_other_option(self, option: str) -> None:
        self.other_options = f"{self.other_options} {option}" if self.other_options else option

    def apply_other_options(self, launcher_params: LauncherParametersDTO) -> None:
        other_options = launcher_params.other_options or ""
        options = other_options.split() if other_options else []
        options = [re.sub("[^a-zA-Z0-9_,-]", "", opt) for opt in options]
        self.other_options = " ".join(options)

    def apply_xpansion_mode(self, launcher_params: LauncherParametersDTO) -> None:
        if launcher_params.xpansion:  # not None and not False
            self.xpansion_mode = {True: "r", False: "cpp"}[launcher_params.xpansion_r_version]
            if (
                isinstance(launcher_params.xpansion, XpansionParametersDTO)
                and launcher_params.xpansion.sensitivity_mode
            ):
                self._append_other_option("xpansion_sensitivity")

    def apply_time_limit(self, launcher_params: LauncherParametersDTO, time_limit_cfg: TimeLimitConfig) -> None:
        # The `time_limit` parameter could be `None`, in that case, the default value is used.
        min_allowed = time_limit_cfg.min * 3600
        max_allowed = time_limit_cfg.max * 3600
        time_limit = launcher_params.time_limit or time_limit_cfg.default * 3600
        time_limit = min(max(time_limit, min_allowed), max_allowed)
        if self.time_limit != time_limit:
            logger.warning(
                f"Invalid slurm launcher time_limit ({time_limit}),"
                f" should be between {min_allowed} and {max_allowed} (in seconds)"
            )
        self.time_limit = time_limit

    def apply_nb_cpu(self, launcher_params: LauncherParametersDTO, nb_cores_cfg: NbCoresConfig) -> None:
        nb_cpu = launcher_params.nb_cpu
        if nb_cpu is not None:
            if nb_cores_cfg.min <= nb_cpu <= nb_cores_cfg.max:
                self.n_cpu = nb_cpu
            else:
                logger.warning(
                    f"Invalid slurm launcher nb_cpu ({nb_cpu}),"
                    f" should be between {nb_cores_cfg.min} and {nb_cores_cfg.max}"
                )
                self.n_cpu = nb_cores_cfg.default

    def apply_post_processing(self, launcher_params: LauncherParametersDTO) -> None:
        post_processing = launcher_params.post_processing
        if post_processing is not None:
            self.post_processing = post_processing

    def apply_adequacy_patch(self, launcher_params: LauncherParametersDTO) -> None:
        adequacy_patch = launcher_params.adequacy_patch
        if adequacy_patch is not None:
            self.post_processing = True


class SlurmLauncher(AbstractLauncher):
    def __init__(
        self,
        config: SlurmConfig,
        callbacks: LauncherCallbacks,
        event_bus: IEventBus,
        cache: ICache,
        use_private_workspace: bool = True,
        retrieve_existing_jobs: bool = False,
    ) -> None:
        if not isinstance(config, SlurmConfig):
            raise TypeError(f"Launcher {config.id} is not a SlurmConfig")
        super().__init__(config, callbacks, event_bus, cache)
        self.config: SlurmConfig = self.config
        self.check_state: bool = True
        self.event_bus = event_bus
        self.event_bus.add_listener(self._create_event_listener(), [EventType.STUDY_JOB_CANCEL_REQUEST])
        self.thread: Optional[threading.Thread] = None
        self.job_list: List[str] = []
        self._check_config()
        self.antares_launcher_lock = threading.Lock()

        # use an absolute path instead of `LOCK_FILE_NAME`:
        local_workspace_dir = Path(self.config.local_workspace)
        with FileLock(local_workspace_dir.joinpath(LOCK_FILE_NAME)):
            self.local_workspace = self._init_workspace(use_private_workspace)
        self.log_tail_manager = LogTailManager(local_workspace_dir)

        self.launcher_args = self._init_launcher_arguments(self.local_workspace)
        self.launcher_params = self._init_launcher_parameters(self.local_workspace)

        self.data_repo_tinydb = DataRepoTinydb(
            database_file_path=(self.launcher_params.json_dir / self.launcher_params.default_json_db_name),
            db_primary_key=self.launcher_params.db_primary_key,
        )
        if retrieve_existing_jobs:
            self._retrieve_running_jobs()

    def _check_config(self) -> None:
        assert_this(
            self.config.local_workspace.exists() and self.config.local_workspace.is_dir()
        )  # and check write permission

    def _init_workspace(self, use_private_workspace: bool) -> Path:
        if not use_private_workspace:
            return Path(self.config.local_workspace)

        for existing_workspace in self.config.local_workspace.iterdir():
            lock_file = existing_workspace / WORKSPACE_LOCK_FILE_NAME
            if (
                existing_workspace.is_dir()
                and existing_workspace != self.config.local_workspace / LOG_DIR_NAME
                and not lock_file.exists()
            ):
                logger.info(f"Initiating slurm workspace into existing directory {existing_workspace}")
                lock_file.touch()
                return existing_workspace

        new_workspace = Path(tempfile.mkdtemp(dir=str(self.config.local_workspace)))
        lock_file = new_workspace / WORKSPACE_LOCK_FILE_NAME
        lock_file.touch()
        logger.info(f"Initiating slurm workspace in new directory {new_workspace}")
        return new_workspace

    def _retrieve_running_jobs(self) -> None:
        if len(self.data_repo_tinydb.get_list_of_studies()) > 0:
            logger.info("Old job retrieved, starting loop")
            self.start()

    def _loop(self) -> None:
        # The loop is executed as admin user
        # It could be more accurate to execute each part
        # of the processing as the user that launched the job
        with current_user_context(DEFAULT_ADMIN_USER):
            while self.check_state:
                # noinspection PyBroadException
                try:
                    self._check_studies_state()
                except Exception:
                    # To keep the SLURM processing monitoring loop active, exceptions
                    # are caught and a message is simply displayed in the logs.
                    logger.error(
                        "An uncaught exception occurred in slurm_launcher loop",
                        exc_info=True,
                    )
                time.sleep(2)

    def start(self) -> None:
        logger.info("Starting slurm_launcher loop")
        self.check_state = True
        self.thread = threading.Thread(
            target=self._loop,
            name=self.__class__.__name__,
            daemon=True,
        )
        self.thread.start()

    def stop(self) -> None:
        self.check_state = False
        self.thread = None
        logger.info("slurm_launcher loop stopped")

    def _init_launcher_arguments(self, local_workspace: Optional[Path] = None) -> argparse.Namespace:
        main_options_parameters = ParserParameters(
            default_wait_time=self.config.default_wait_time,
            default_time_limit=self.config.time_limit.default * 3600,
            default_n_cpu=self.config.nb_cores.default,
            studies_in_dir=str((Path(local_workspace or self.config.local_workspace) / STUDIES_INPUT_DIR_NAME)),
            log_dir=str((Path(self.config.local_workspace) / LOG_DIR_NAME)),
            finished_dir=str((Path(local_workspace or self.config.local_workspace) / STUDIES_OUTPUT_DIR_NAME)),
            ssh_config_file_is_required=False,
            ssh_configfile_path_alternate1=None,
            ssh_configfile_path_alternate2=None,
        )

        parser: MainOptionParser = MainOptionParser(main_options_parameters)
        parser.add_basic_arguments()
        parser.add_advanced_arguments()

        arguments = cast(argparse.Namespace, parser.parse_args([]))
        arguments.wait_mode = False
        arguments.check_queue = False
        arguments.json_ssh_config = None
        arguments.job_id_to_kill = None
        arguments.xpansion_mode = None
        arguments.version = False
        arguments.post_processing = False
        arguments.other_options = None

        return arguments

    def _init_launcher_parameters(self, local_workspace: Optional[Path] = None) -> MainParameters:
        return MainParameters(
            json_dir=local_workspace or self.config.local_workspace,
            default_json_db_name=self.config.default_json_db_name,
            slurm_script_path=self.config.slurm_script_path,
            partition=self.config.partition,
            antares_versions_on_remote_server=self.config.antares_versions_on_remote_server,
            default_ssh_dict={
                "username": self.config.username,
                "hostname": self.config.hostname,
                "port": self.config.port,
                "private_key_file": self.config.private_key_file,
                "key_password": self.config.key_password,
                "password": self.config.password,
            },
            db_primary_key="name",
        )

    def _delete_workspace_file(self, study_path: Path) -> None:
        if self.local_workspace.absolute() in study_path.absolute().parents and study_path.exists():
            logger.info(f"Deleting workspace file at {study_path}")
            if study_path.is_dir():
                shutil.rmtree(study_path)
            else:
                os.unlink(study_path)

    def _import_study_output(
        self,
        job_id: str,
        xpansion_mode: Optional[str] = None,
        log_dir: Optional[str] = None,
    ) -> Optional[str]:
        if xpansion_mode:
            self._import_xpansion_result(job_id, xpansion_mode)

        launcher_logs: Dict[str, List[Path]] = {}
        if log_dir is not None:
            launcher_logs = {
                log_name: log_path
                for log_name, log_path in {
                    "antares-out.log": [
                        p
                        for p in [SlurmLauncher._get_log_path_from_log_dir(Path(log_dir), LogType.STDOUT)]
                        if p is not None
                    ],
                    "antares-err.log": [
                        p
                        for p in [SlurmLauncher._get_log_path_from_log_dir(Path(log_dir), LogType.STDERR)]
                        if p is not None
                    ],
                }.items()
                if log_path
            }

        # The following callback is actually calling:
        # `antarest.launcher.service.LauncherService._import_output`
        return self.callbacks.import_output(
            job_id,
            self.local_workspace / STUDIES_OUTPUT_DIR_NAME / job_id / "output",
            launcher_logs,
        )

    def _import_xpansion_result(self, job_id: str, xpansion_mode: str) -> None:
        output_path = self.local_workspace / STUDIES_OUTPUT_DIR_NAME / job_id / "output"
        if output_path.exists() and len(os.listdir(output_path)) == 1:
            output_path = output_path / os.listdir(output_path)[0]
            if output_path.name.endswith(".zip"):
                logger.info("Unzipping zipped output for xpansion result storage")
                unzipped_output_path = (
                    self.local_workspace / STUDIES_OUTPUT_DIR_NAME / job_id / "output" / output_path.name[:-4]
                )
                unzip(
                    unzipped_output_path,
                    output_path,
                    remove_source_zip=True,
                )
                output_path = unzipped_output_path

            if xpansion_mode == "r":
                shutil.copytree(
                    self.local_workspace / STUDIES_OUTPUT_DIR_NAME / job_id / "user" / "expansion",
                    output_path / "results",
                )
        else:
            logger.warning("Output path in xpansion result not found")

    def _check_studies_state(self) -> None:
        with self.antares_launcher_lock:
            try:
                self._call_launcher(
                    arguments=self.launcher_args,
                    parameters=self.launcher_params,
                )
            except Exception as e:
                logger.info("Could not get data on remote server", exc_info=e)

            study_list = self.data_repo_tinydb.get_list_of_studies()
            for study in study_list:
                log_path = SlurmLauncher._get_log_path(study)
                if study.with_error:
                    self.log_tail_manager.stop_tracking(log_path)
                    self._handle_failure(study)
                elif study.done:
                    self.log_tail_manager.stop_tracking(log_path)
                    self._handle_success(study)
                else:
                    # study.started => still running
                    # study.finished => waiting for ZIP + logs retrieval (or failure)
                    self.log_tail_manager.track(log_path, self.create_update_log(study.name))

            # Re-fetching the study list is necessary as new studies may have been added
            # during the `import_output` process. Afterward, we clean up the list to ensure
            # that any removed studies are removed from the database.

            cleanup_list = [s for s in study_list if s.with_error or s.done]
            for study in cleanup_list:
                self._clean_up_study(study.name)
            updated_list = self.data_repo_tinydb.get_list_of_studies()
            if {s.name for s in updated_list} == {s.name for s in cleanup_list}:
                self.stop()

    def _handle_failure(self, study: StudyDTO) -> None:
        """
        The simulation failed (`study.with_error == True`),
        we can try to download output results,
        but we expect to find no `output` directory

        Args:
            study: Study extracted from the SLURM database.
        """
        # sourcery skip: extract-duplicate-method
        try:
            output_id = self._import_study_output(
                study.name,
                study.xpansion_mode,
                study.job_log_dir,
            )
        except FileNotFoundError:
            msg = "Simulation failed, output results are not available"
            self.callbacks.append_after_log(study.name, msg)
            # see antarest.launcher.service.LauncherService.update
            self.callbacks.update_status(study.name, JobStatus.FAILED, msg, None)
        except Exception as e:
            stack_trace = traceback.format_exc()
            msg = (
                f"An error occurred unexpectedly while trying to import the study output:"
                f" {study.name=}, {study.xpansion_mode=}, {study.job_log_dir=},"
                f" see stack trace below:\n{stack_trace}"
            )
            self.callbacks.append_after_log(study.name, msg)
            self.callbacks.update_status(study.name, JobStatus.FAILED, msg, None)
            logger.error(msg, exc_info=e)
        else:
            msg = "Simulation failed (even if some output results may be available)"
            self.callbacks.append_after_log(study.name, msg)
            self.callbacks.update_status(study.name, JobStatus.FAILED, msg, output_id)

    def _handle_success(self, study: StudyDTO) -> None:
        """
        The simulation succeed (`study.done == True`),
        in that case, we have the guarantee that:

        - logs are downloaded,
        - result ZIPs are downloaded and unarchived to `output`,
        - the server is clean (a.k.a. input and output ZIPs are removed from remote)

        Args:
            study: Study extracted from the SLURM database.
        """
        try:
            output_id = self._import_study_output(
                study.name,
                study.xpansion_mode,
                study.job_log_dir,
            )
        except Exception as e:
            stack_trace = traceback.format_exc()
            msg = (
                f"An error occurred unexpectedly while importing the study output:"
                f" {study.name=}, {study.xpansion_mode=}, {study.job_log_dir=},"
                f" see stack trace below:\n{stack_trace}"
            )
            self.callbacks.append_after_log(study.name, msg)
            self.callbacks.update_status(study.name, JobStatus.FAILED, msg, None)
            logger.error(msg, exc_info=e)
        else:
            self.callbacks.update_status(study.name, JobStatus.SUCCESS, None, output_id)

    @staticmethod
    def _get_log_path(study: StudyDTO, log_type: LogType = LogType.STDOUT) -> Optional[Path]:
        log_dir = Path(study.job_log_dir)
        return SlurmLauncher._get_log_path_from_log_dir(log_dir, log_type)

    @staticmethod
    def _find_log_dir(base_log_dir: Path, job_id: str) -> Optional[Path]:
        pattern = f"{job_id}*"
        return next(iter(base_log_dir.glob(pattern)), None)

    @staticmethod
    def _get_log_path_from_log_dir(log_dir: Path, log_type: LogType = LogType.STDOUT) -> Optional[Path]:
        pattern = {
            LogType.STDOUT: "antares-out-*",
            LogType.STDERR: "antares-err-*",
        }[log_type]
        return next(iter(log_dir.glob(pattern)), None)

    def _clean_local_workspace(self) -> None:
        logger.info("Cleaning up slurm workspace")
        local_workspace = self.local_workspace
        for filename in os.listdir(local_workspace):
            file_path = os.path.join(local_workspace, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)

    def _clean_up_study(self, launch_id: str) -> None:
        logger.info(f"Cleaning up study with launch_id {launch_id}")
        self.data_repo_tinydb.remove_study(launch_id)
        self._delete_workspace_file(self.local_workspace / STUDIES_OUTPUT_DIR_NAME / launch_id)
        self._delete_workspace_file(self.local_workspace / STUDIES_INPUT_DIR_NAME / launch_id)
        if (self.local_workspace / STUDIES_OUTPUT_DIR_NAME).exists():
            for finished_zip in (self.local_workspace / STUDIES_OUTPUT_DIR_NAME).iterdir():
                if finished_zip.is_file() and re.match(f"finished_(XPANSION_)?{launch_id}_\\d+", finished_zip.name):
                    self._delete_workspace_file(finished_zip)

    def _run_study(
        self,
        study_uuid: str,
        launch_uuid: str,
        launcher_params: LauncherParametersDTO,
        version: SolverVersion,
    ) -> None:
        study_path = Path(self.launcher_args.studies_in) / launch_uuid

        # `append_log` is a function alias for readability ;-)
        append_log = self.callbacks.append_before_log

        with self.antares_launcher_lock:
            # noinspection PyBroadException
            try:
                # export study
                append_log(launch_uuid, "Exporting study...")
                self.callbacks.export_study(launch_uuid, study_uuid, study_path, launcher_params)

                append_log(launch_uuid, "Checking study version...")
                available_versions = self.config.antares_versions_on_remote_server
                if f"{version:ddd}" not in available_versions:
                    raise VersionNotSupportedError(
                        f"Study version '{version}' is not supported. Currently supported versions are"
                        f" {', '.join(available_versions)}"
                    )
                _override_solver_version(study_path, version)

                append_log(launch_uuid, "Submitting study to slurm launcher")
                launcher_args = self._apply_params(launcher_params)
                self._call_launcher(launcher_args, self.launcher_params)

                launch_success = self._check_if_study_is_in_launcher_db(launch_uuid)
                if launch_success:
                    append_log(launch_uuid, "Study submitted")
                    logger.info("Study exported and run with launcher")
                else:
                    self.callbacks.append_after_log(
                        launch_uuid,
                        "Study not submitted. The study configuration may be incorrect",
                    )
                    logger.warning(f"Study {study_uuid} with job id {launch_uuid} does not seem to have been launched")

                self.callbacks.update_status(
                    launch_uuid,
                    JobStatus.RUNNING if launch_success else JobStatus.FAILED,
                    None,
                    None,
                )
            except Exception as e:
                stack_trace = traceback.format_exc()
                msg = f"Failed to launch study {study_uuid}: see stack trace below:\n{stack_trace}"
                self.callbacks.append_after_log(launch_uuid, msg)
                self.callbacks.update_status(launch_uuid, JobStatus.FAILED, msg, None)
                self._clean_up_study(launch_uuid)
                logger.error(msg, exc_info=e)
                raise
            finally:
                self._delete_workspace_file(study_path)

        if not self.thread:
            self.start()

    def _call_launcher(self, arguments: argparse.Namespace, parameters: MainParameters) -> None:
        run_with(arguments, parameters, show_banner=False)

    def _check_if_study_is_in_launcher_db(self, job_id: str) -> bool:
        studies = self.data_repo_tinydb.get_list_of_studies()
        return any(s.name == job_id for s in studies)

    def _apply_params(self, launcher_params: LauncherParametersDTO) -> argparse.Namespace:
        """
        Populate a `argparse.Namespace` object with the user parameters.

        Args:
            launcher_params:
                Contains the launcher parameters selected by the user.
                If a parameter is not provided (`None`), the default value should be retrieved
                from the configuration.

        Returns:
            The `argparse.Namespace` object which is then passed to `antarestlauncher.main.run_with`,
            to launch a simulation using Antares Launcher.
        """
        if launcher_params:
            launcher_args = LauncherArgs(self.launcher_args)
            launcher_args.apply_other_options(launcher_params)
            launcher_args.apply_xpansion_mode(launcher_params)
            launcher_args.apply_time_limit(launcher_params, self.config.time_limit)
            launcher_args.apply_post_processing(launcher_params)
            launcher_args.apply_nb_cpu(launcher_params, self.config.nb_cores)
            launcher_args.apply_adequacy_patch(launcher_params)
            return launcher_args

        return self.launcher_args

    @override
    def run_study(
        self, study_uuid: str, job_id: str, version: SolverVersion, launcher_parameters: LauncherParametersDTO
    ) -> None:
        thread = threading.Thread(
            target=self._run_study,
            args=(study_uuid, job_id, launcher_parameters, version),
            name=f"{self.__class__.__name__}-JobRunner",
        )
        thread.start()

    @override
    def get_log(self, job_id: str, log_type: LogType) -> Optional[str]:
        log_path: Optional[Path] = None
        for study in self.data_repo_tinydb.get_list_of_studies():
            if study.name == job_id:
                log_path = SlurmLauncher._get_log_path(study, log_type)
                if log_path:
                    return log_path.read_text()
        if log_dir := SlurmLauncher._find_log_dir(Path(self.launcher_args.log_dir) / "JOB_LOGS", job_id):
            log_path = SlurmLauncher._get_log_path_from_log_dir(log_dir, log_type)
        return log_path.read_text() if log_path else None

    def _create_event_listener(self) -> Callable[[Event], Awaitable[None]]:
        async def _listen_to_kill_job(event: Event) -> None:
            self.kill_job(event.payload, dispatch=False)

        return _listen_to_kill_job

    @override
    def kill_job(self, job_id: str, dispatch: bool = True) -> None:
        launcher_args = LauncherArgs(self.launcher_args)
        for study in self.data_repo_tinydb.get_list_of_studies():
            if study.name == job_id:
                launcher_args.job_id_to_kill = study.job_id
                logger.info(f"Cancelling job {job_id} (dispatched={not dispatch})")
                with self.antares_launcher_lock:
                    self._call_launcher(launcher_args, self.launcher_params)
                return
        if dispatch:
            self.event_bus.push(
                Event(
                    type=EventType.STUDY_JOB_CANCEL_REQUEST,
                    payload=job_id,
                    permissions=PermissionInfo(public_mode=PublicMode.NONE),
                )
            )
            self.callbacks.update_status(
                job_id,
                JobStatus.FAILED,
                None,
                None,
            )


def _override_solver_version(study_path: Path, version: SolverVersion) -> None:
    study_info_path = study_path / "study.antares"
    study_info = read_ini(study_info_path)
    if "antares" in study_info:
        if version.major < 9:  # should be written as XYZ
            version_to_write = f"{version:ddd}"
        else:  # should be written as X.Y
            version_to_write = f"{version:2d}"
        study_info["antares"]["solver_version"] = version_to_write
        write_ini_file(study_info_path, study_info)
    else:
        logger.warning("Failed to find antares study info")
