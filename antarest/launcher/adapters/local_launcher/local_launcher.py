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
from antarest.launcher.adapters.abstractlauncher import AbstractLauncher, LauncherCallbacks, LauncherInitException
from antarest.launcher.adapters.log_manager import LogTailManager
from antarest.launcher.model import JobStatus, LauncherParametersDTO, LogType

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
        super().__init__(config, callbacks, event_bus, cache)
        self.local_workspace = config.local_workspace
        logs_path = self.local_workspace / "LOGS"
        logs_path.mkdir(parents=True, exist_ok=True)
        self.log_directory = logs_path
        self.log_tail_manager = LogTailManager(self.local_workspace)
        self.job_id_to_study_id: Dict[str, Tuple[str, Path, subprocess.Popen]] = {}  # type: ignore
        self.logs: Dict[str, str] = {}

    def _select_best_binary(self, version: str) -> Path:
        local = self.config.launcher.local
        if local is None:
            raise LauncherInitException("Missing parameter 'launcher.local'")
        elif version in local.binaries:
            antares_solver_path = local.binaries[version]
        else:
            # sourcery skip: extract-method, max-min-default
            # fixme: `version` must remain a string, consider using a `Version` class
            version_int = int(version)
            keys = list(map(int, local.binaries.keys()))
            keys_sup = [k for k in keys if k > version_int]
            best_existing_version = min(keys_sup) if keys_sup else max(keys)
            antares_solver_path = local.binaries[str(best_existing_version)]
            logger.warning(
                f"Version {version} is not available. Version {best_existing_version} has been selected instead"
            )
        return antares_solver_path

    @override
    def run_study(
        self, study_uuid: str, job_id: str, version: SolverVersion, launcher_parameters: LauncherParametersDTO
    ) -> None:
        antares_solver_path = self._select_best_binary(f"{version:ddd}")

        job = threading.Thread(
            target=LocalLauncher._compute,
            args=(
                self,
                antares_solver_path,
                study_uuid,
                job_id,
                launcher_parameters,
            ),
            name=f"{self.__class__.__name__}-JobRunner",
        )
        job.start()

    def _compute(
        self,
        antares_solver_path: Path,
        study_uuid: str,
        job_id: str,
        launcher_parameters: LauncherParametersDTO,
    ) -> None:
        export_path = self.local_workspace / job_id
        logs_path = self.log_directory / job_id
        logs_path.mkdir()
        try:
            self.callbacks.export_study(job_id, study_uuid, export_path, launcher_parameters)

            simulator_args, environment_variables = self._parse_launcher_options(launcher_parameters)
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
            logger.info(f"Removing launch {job_id} export path at {export_path}")
            shutil.rmtree(export_path, ignore_errors=True)

    def _import_launcher_logs(self, job_id: str) -> Dict[str, List[Path]]:
        logs_path = self.log_directory / job_id
        return {
            "antares-out.log": [logs_path / f"{job_id}-out.log"],
            "antares-err.log": [logs_path / f"{job_id}-err.log"],
        }

    def _parse_launcher_options(self, launcher_parameters: LauncherParametersDTO) -> Tuple[List[str], Dict[str, Any]]:
        simulator_args = [f"--force-parallel={launcher_parameters.nb_cpu}"]
        environment_variables = os.environ.copy()
        if launcher_parameters.other_options:
            solver = []
            if "xpress" in launcher_parameters.other_options:
                solver = ["--use-ortools", "--ortools-solver=xpress"]
                if xpress_dir_path := self.config.launcher.local.xpress_dir:  # type: ignore
                    environment_variables["XPRESSDIR"] = xpress_dir_path
                    environment_variables["XPRESS"] = environment_variables["XPRESSDIR"] + os.sep + "bin"
            elif "coin" in launcher_parameters.other_options:
                solver = ["--use-ortools", "--ortools-solver=coin"]
            if solver:
                simulator_args += solver
            if "presolve" in launcher_parameters.other_options:
                simulator_args += ["--solver-parameters", "PRESOLVE 1"]
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
