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

import logging
import os
import shlex
import shutil
import signal
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from antares.study.version import SolverVersion
from typing_extensions import override

from antarest.core.config import LocalConfig
from antarest.core.interfaces.cache import ICache
from antarest.core.interfaces.eventbus import IEventBus
from antarest.core.jwt import JWTUser
from antarest.launcher.adapters.abstractlauncher import AbstractLauncher, LauncherCallbacks
from antarest.launcher.adapters.log_manager import LogTailManager
from antarest.launcher.model import JobStatus, LauncherLoadDTO, LauncherParametersDTO, LogType
from antarest.login.utils import current_user_context, require_current_user
from antarest.study.model import STUDY_VERSION_9_2

logger = logging.getLogger(__name__)


class LocalLauncher(AbstractLauncher):
    """
    This local launcher is meant to work when using AntaresWeb on a single worker process in local mode
    """

    def __init__(
        self,
        config: LocalConfig,
        callbacks: LauncherCallbacks,
        event_bus: IEventBus,
        cache: ICache,
    ) -> None:
        super().__init__(callbacks, event_bus, cache)
        self.local_config: LocalConfig = config
        self.local_workspace = config.local_workspace
        logs_path = self.local_workspace / "LOGS"
        logs_path.mkdir(parents=True, exist_ok=True)
        self.log_directory = logs_path
        self.log_tail_manager = LogTailManager(self.local_workspace)
        self.submitted_jobs: dict[str, LauncherParametersDTO] = {}
        self.job_id_to_study_id: Dict[str, Tuple[str, Path, subprocess.Popen]] = {}  # type: ignore
        self.logs: Dict[str, str] = {}

    def _select_best_binary(self, version: str) -> Path:
        if version in self.local_config.binaries:
            antares_solver_path = self.local_config.binaries[version]
        else:
            # sourcery skip: extract-method, max-min-default
            # fixme: `version` must remain a string, consider using a `Version` class
            version_int = int(version)
            keys = list(map(int, self.local_config.binaries.keys()))
            keys_sup = [k for k in keys if k > version_int]
            best_existing_version = min(keys_sup) if keys_sup else max(keys)
            antares_solver_path = self.local_config.binaries[str(best_existing_version)]
            logger.warning(
                f"Version {version} is not available. Version {best_existing_version} has been selected instead"
            )
        return antares_solver_path

    @override
    def run_study(
        self, study_uuid: str, job_id: str, version: SolverVersion, launcher_parameters: LauncherParametersDTO
    ) -> None:
        antares_solver_path = self._select_best_binary(f"{version:ddd}")
        self.submitted_jobs[job_id] = launcher_parameters

        job = threading.Thread(
            target=LocalLauncher._compute,
            args=(self, antares_solver_path, study_uuid, job_id, launcher_parameters, version, require_current_user()),
            name=f"{self.__class__.__name__}-JobRunner",
        )
        job.start()

    def _compute(
        self,
        antares_solver_path: Path,
        study_uuid: str,
        job_id: str,
        launcher_parameters: LauncherParametersDTO,
        version: SolverVersion,
        current_user: JWTUser,
    ) -> None:
        with current_user_context(current_user):
            export_path = self.local_workspace / job_id
            logs_path = self.log_directory / job_id
            logs_path.mkdir()
            try:
                self.callbacks.export_study(job_id, study_uuid, export_path, launcher_parameters)

                simulator_args, environment_variables = self._parse_launcher_options(launcher_parameters, version)
                new_args = [str(antares_solver_path)] + simulator_args + [str(export_path)]

                std_err_file = logs_path / f"{job_id}-err.log"
                std_out_file = logs_path / f"{job_id}-out.log"
                with open(std_err_file, "w") as err_file, open(std_out_file, "w") as out_file:
                    process = subprocess.Popen(
                        new_args,
                        env=environment_variables,
                        stdout=out_file,
                        stderr=err_file,
                        universal_newlines=True,
                        encoding="utf-8",
                    )
                self.job_id_to_study_id[job_id] = (study_uuid, export_path, process)
                self.callbacks.update_status(job_id, JobStatus.RUNNING, None, None)

                self.log_tail_manager.track(std_out_file, self.create_update_log(job_id))

                while process.poll() is None:
                    time.sleep(1)

                if launcher_parameters is not None and (
                    launcher_parameters.post_processing or launcher_parameters.adequacy_patch is not None
                ):
                    subprocess.run(["Rscript", "post-processing.R"], cwd=export_path)

                output_id: Optional[str] = None
                if process.returncode == 0:
                    # The job succeed we need to import the output
                    try:
                        launcher_logs = self._import_launcher_logs(job_id)
                        output_id = self.callbacks.import_output(job_id, export_path / "output", launcher_logs)
                    except Exception as e:
                        logger.error(
                            f"Failed to import output for study {study_uuid} located at {export_path}",
                            exc_info=e,
                        )
                del self.job_id_to_study_id[job_id]
                self.callbacks.update_status(
                    job_id,
                    JobStatus.FAILED if process.returncode != 0 or not output_id else JobStatus.SUCCESS,
                    None,
                    output_id,
                )
            except Exception as e:
                logger.error(f"Unexpected error happened during launch {job_id}", exc_info=e)
                self.callbacks.update_status(
                    job_id,
                    JobStatus.FAILED,
                    str(e),
                    None,
                )
            finally:
                del self.submitted_jobs[job_id]
                logger.info(f"Removing launch {job_id} export path at {export_path}")
                shutil.rmtree(export_path, ignore_errors=True)

    def _import_launcher_logs(self, job_id: str) -> Dict[str, List[Path]]:
        logs_path = self.log_directory / job_id
        return {
            "antares-out.log": [logs_path / f"{job_id}-out.log"],
            "antares-err.log": [logs_path / f"{job_id}-err.log"],
        }

    def _parse_launcher_options(
        self, launcher_parameters: LauncherParametersDTO, version: SolverVersion
    ) -> Tuple[List[str], Dict[str, Any]]:
        simulator_args = [f"--force-parallel={launcher_parameters.nb_cpu}"] if launcher_parameters.nb_cpu else []
        environment_variables = os.environ.copy()
        if not launcher_parameters.other_options:
            return simulator_args, environment_variables

        # Split other options
        options = shlex.split(launcher_parameters.other_options)

        # Use solver logs
        if "solver-logs" in options:
            simulator_args += ["--solver-logs"]

        # Call the right solver
        solver = ""
        if "xpress" in options:
            solver = "xpress"
        elif "coin" in options:
            solver = "coin"
        if solver:
            if version >= STUDY_VERSION_9_2:
                simulator_args += [f"--solver={solver}"]
            else:
                simulator_args.extend(["--use-ortools", f"--ortools-solver={solver}"])

        # 'xpress' specific part
        if "xpress" in options:
            # Load environment variables
            if xpress_dir_path := self.local_config.xpress_dir:
                environment_variables["XPRESSDIR"] = xpress_dir_path
                environment_variables["XPRESS"] = environment_variables["XPRESSDIR"] + os.sep + "bin"

            # Parse specific options
            if "nobasis1" in options:
                simulator_args += ["--use-optim-1-basis-next-week=false"]
            if "nobasis2" in options:
                simulator_args += ["--use-optim-1-basis-optim-2=false"]

            solver_parameters_optim1 = []
            solver_parameters_optim2 = []
            if "presolve" in options:
                solver_parameters_optim1 += ["PRESOLVE 1"]
                solver_parameters_optim2 += ["PRESOLVE 1"]
            for opt in options:
                if opt.startswith("param-optim1="):
                    solver_parameters_optim1 += [opt.removeprefix("param-optim1=")]
                if opt.startswith("param-optim2="):
                    solver_parameters_optim2 += [opt.removeprefix("param-optim2=")]
            if solver_parameters_optim1:
                simulator_args += [f'--lp-solver-param-optim-1="{" ".join(solver_parameters_optim1)}"']
            if solver_parameters_optim2:
                simulator_args += [f'--lp-solver-param-optim-2="{" ".join(solver_parameters_optim2)}"']

        return simulator_args, environment_variables

    @override
    def create_update_log(self, job_id: str) -> Callable[[str], None]:
        base_func = super().create_update_log(job_id)
        self.logs[job_id] = ""

        def append_to_log(log_line: str) -> None:
            base_func(log_line)
            self.logs[job_id] += log_line + "\n"

        return append_to_log

    @override
    def get_log(self, job_id: str, log_type: LogType) -> Optional[str]:
        if job_id in self.job_id_to_study_id and job_id in self.logs and log_type == LogType.STDOUT:
            return self.logs[job_id]
        job_path = self.log_directory / job_id / f"{job_id}-{log_type.to_suffix()}"
        if job_path.exists():
            return job_path.read_text()
        return None

    @override
    def kill_job(self, job_id: str) -> None:
        if job_id in self.job_id_to_study_id:
            return self.job_id_to_study_id[job_id][2].send_signal(signal.SIGTERM)
        else:
            self.callbacks.update_status(
                job_id,
                JobStatus.FAILED,
                None,
                None,
            )

    @override
    def get_solver_versions(self) -> List[str]:
        return sorted(self.local_config.binaries)

    @override
    def get_load(self) -> LauncherLoadDTO:
        local_used_cpus = sum(params.nb_cpu or 1 for params in self.submitted_jobs.values())

        # The cluster load is approximated by the percentage of used CPUs.
        cluster_load_approx = min(100.0, 100 * local_used_cpus / (os.cpu_count() or 1))

        args = {
            "allocatedCpuRate": cluster_load_approx,
            "clusterLoadRate": cluster_load_approx,
            "nbQueuedJobs": 0,
            "launcherStatus": "SUCCESS",
        }
        return LauncherLoadDTO(**args)
