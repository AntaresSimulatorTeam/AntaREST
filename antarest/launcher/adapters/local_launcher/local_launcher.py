# Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import io
import logging
import shutil
import signal
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from typing import Callable, Dict, Optional, Tuple, cast
from uuid import UUID

from antares.study.version import SolverVersion

from antarest.core.config import Config
from antarest.core.interfaces.cache import ICache
from antarest.core.interfaces.eventbus import IEventBus
from antarest.core.requests import RequestParameters
from antarest.launcher.adapters.abstractlauncher import AbstractLauncher, LauncherCallbacks, LauncherInitException
from antarest.launcher.adapters.log_manager import follow
from antarest.launcher.model import JobStatus, LauncherParametersDTO, LogType

logger = logging.getLogger(__name__)


class LocalLauncher(AbstractLauncher):
    """
    This local launcher is meant to work when using AntaresWeb on a single worker process in local mode
    """

    def __init__(
        self,
        config: Config,
        callbacks: LauncherCallbacks,
        event_bus: IEventBus,
        cache: ICache,
    ) -> None:
        super().__init__(config, callbacks, event_bus, cache)
        if self.config.launcher.local is None:
            raise LauncherInitException("Missing parameter 'launcher.local'")
        self.tmpdir = config.storage.tmp_dir
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

    def run_study(
        self,
        study_uuid: str,
        job_id: str,
        version: SolverVersion,
        launcher_parameters: LauncherParametersDTO,
        params: RequestParameters,
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

    def _get_job_final_output_path(self, job_id: str) -> Path:
        return self.config.storage.tmp_dir / f"antares_solver-{job_id}.log"

    def _compute(
        self,
        antares_solver_path: Path,
        study_uuid: str,
        uuid: UUID,
        launcher_parameters: LauncherParametersDTO,
    ) -> None:
        end = False

        def stop_reading_output() -> bool:
            if end and str(uuid) in self.logs:
                with open(
                    self._get_job_final_output_path(str(uuid)),
                    "w",
                ) as log_file:
                    log_file.write(self.logs[str(uuid)])
                del self.logs[str(uuid)]
            return end

        tmp_path = tempfile.mkdtemp(prefix="local_launch_", dir=str(self.tmpdir))
        export_path = Path(tmp_path) / "export"
        try:
            self.callbacks.export_study(str(uuid), study_uuid, export_path, launcher_parameters)

            simulator_args = [f"--force-parallel={launcher_parameters.nb_cpu}"]
            if launcher_parameters.other_options:
                solver = []
                if "xpress" in launcher_parameters.other_options:
                    solver = ["--use-ortools", "--ortools-solver=xpress"]
                elif "coin" in launcher_parameters.other_options:
                    solver = ["--use-ortools", "--ortools-solver=coin"]
                if solver:
                    simulator_args += solver
                if "presolve" in launcher_parameters.other_options:
                    simulator_args.append('--solver-parameters="PRESOLVE 1"')

            new_args = [str(antares_solver_path)] + simulator_args + [str(export_path)]
            process = subprocess.Popen(
                new_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                encoding="utf-8",
            )
            self.job_id_to_study_id[str(uuid)] = (
                study_uuid,
                export_path,
                process,
            )
            self.callbacks.update_status(
                str(uuid),
                JobStatus.RUNNING,
                None,
                None,
            )

            thread = threading.Thread(
                target=lambda: follow(
                    cast(io.StringIO, process.stdout),
                    self.create_update_log(str(uuid)),
                    stop_reading_output,
                    None,
                ),
                name=f"{self.__class__.__name__}-LogsWatcher",
                daemon=True,
            )
            thread.start()

            while process.poll() is None:
                time.sleep(1)

            if launcher_parameters is not None and (
                launcher_parameters.post_processing or launcher_parameters.adequacy_patch is not None
            ):
                subprocess.run(["Rscript", "post-processing.R"], cwd=export_path)

            output_id: Optional[str] = None
            try:
                output_id = self.callbacks.import_output(str(uuid), export_path / "output", {})
            except Exception as e:
                logger.error(
                    f"Failed to import output for study {study_uuid} located at {export_path}",
                    exc_info=e,
                )
            del self.job_id_to_study_id[str(uuid)]
            self.callbacks.update_status(
                str(uuid),
                JobStatus.FAILED if process.returncode != 0 or not output_id else JobStatus.SUCCESS,
                None,
                output_id,
            )
        except Exception as e:
            logger.error(f"Unexpected error happened during launch {uuid}", exc_info=e)
            self.callbacks.update_status(
                str(uuid),
                JobStatus.FAILED,
                str(e),
                None,
            )
        finally:
            logger.info(f"Removing launch {uuid} export path at {tmp_path}")
            end = True
            shutil.rmtree(tmp_path)

    def create_update_log(self, job_id: str) -> Callable[[str], None]:
        base_func = super().create_update_log(job_id)
        self.logs[job_id] = ""

        def append_to_log(log_line: str) -> None:
            base_func(log_line)
            self.logs[job_id] += log_line + "\n"

        return append_to_log

    def get_log(self, job_id: str, log_type: LogType) -> Optional[str]:
        if job_id in self.job_id_to_study_id and job_id in self.logs:
            return self.logs[job_id]
        elif self._get_job_final_output_path(job_id).exists():
            return self._get_job_final_output_path(job_id).read_text()
        return None

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
