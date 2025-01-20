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

import contextlib
import shlex
import socket
from typing import Any, List, Tuple

import paramiko

from antarest.launcher.ssh_config import SSHConfigDTO


@contextlib.contextmanager  # type: ignore
def ssh_client(ssh_config: SSHConfigDTO) -> paramiko.SSHClient:  # type: ignore
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=ssh_config.hostname,
        port=ssh_config.port,
        username=ssh_config.username,
        pkey=paramiko.RSAKey.from_private_key_file(filename=str(ssh_config.private_key_file)),
        timeout=600,
        allow_agent=False,
    )
    with contextlib.closing(client):
        yield client


class SlurmError(Exception):
    pass


def execute_command(ssh_config: SSHConfigDTO, args: List[str]) -> Any:
    command = " ".join(args)
    try:
        with ssh_client(ssh_config) as client:  # type: paramiko.SSHClient
            _, stdout, stderr = client.exec_command(command, timeout=10)
            output = stdout.read().decode("utf-8").strip()
            error = stderr.read().decode("utf-8").strip()
    except (
        paramiko.AuthenticationException,
        paramiko.SSHException,
        socket.timeout,
        socket.error,
    ) as e:
        raise SlurmError(f"Can't retrieve SLURM information: {e}") from e
    if error:
        raise SlurmError(f"Can't retrieve SLURM information: {error}")
    return output


def parse_cpu_used(sinfo_output: str) -> float:
    """
    Returns the percentage of used CPUs in the cluster, in range [0, 100].
    """
    cpu_info_split = sinfo_output.split("/")
    cpu_used_count = int(cpu_info_split[0])
    cpu_inactive_count = int(cpu_info_split[1])
    return 100 * cpu_used_count / (cpu_used_count + cpu_inactive_count)


def parse_cpu_load(sinfo_output: str) -> float:
    """
    Returns the percentage of CPU load in the cluster, in range [0, 100].
    """
    lines = sinfo_output.splitlines()
    cpus_used = 0.0
    cpus_available = 0.0
    for line in lines:
        values = line.split()
        if "N/A" in values:
            continue
        cpus_used += float(values[0])
        cpus_available += float(values[1])
    ratio = cpus_used / max(cpus_available, 1)
    return 100 * min(1.0, ratio)


def calculates_slurm_load(ssh_config: SSHConfigDTO, partition: str) -> Tuple[float, float, int]:
    """
    Returns the used/oad of the SLURM cluster or local machine in percentage and the number of queued jobs.

    Args:
        ssh_config: SSH configuration to connect to the SLURM server.
        partition: Name of the partition to query, or empty string to query all partitions.

    Returns:
        - percentage of used CPUs in the cluster, in range [0, 100]
        - percentage of CPU load in the cluster, in range [0, 100]
        - number of queued jobs
    """
    partition_arg = f"--partition={partition}" if partition else ""

    # allocated cpus
    arg_list = ["sinfo", partition_arg, "-O", "NodeAIOT", "--noheader"]
    sinfo_cpus_used = execute_command(ssh_config, arg_list)
    if not sinfo_cpus_used:
        args = " ".join(map(shlex.quote, arg_list))
        raise SlurmError(f"Can't retrieve SLURM information: [{args}] returned no result")
    allocated_cpus = parse_cpu_used(sinfo_cpus_used)

    # cluster load
    arg_list = ["sinfo", partition_arg, "-N", "-O", "CPUsLoad,CPUs", "--noheader"]
    sinfo_cpus_load = execute_command(ssh_config, arg_list)
    if not sinfo_cpus_load:
        args = " ".join(map(shlex.quote, arg_list))
        raise SlurmError(f"Can't retrieve SLURM information: [{args}] returned no result")
    cluster_load = parse_cpu_load(sinfo_cpus_load)

    # queued jobs
    arg_list = ["squeue", partition_arg, "--noheader", "-t", "pending", "|", "wc", "-l"]
    queued_jobs = execute_command(ssh_config, arg_list)
    if not queued_jobs:
        args = " ".join(map(shlex.quote, arg_list))
        raise SlurmError(f"Can't retrieve SLURM information: [{args}] returned no result")

    return allocated_cpus, cluster_load, int(queued_jobs)
