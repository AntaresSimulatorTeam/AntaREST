import contextlib
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
        with ssh_client(ssh_config) as client:  # type: ignore
            stdin, stdout, stderr = client.exec_command(command, timeout=10)
            output = stdout.read().decode("utf-8").strip()
            error = stderr.read().decode("utf-8").strip()
    except (
        paramiko.AuthenticationException,
        paramiko.SSHException,
        socket.timeout,
        socket.error,
    ) as e:
        raise SlurmError("Can't retrieve SLURM information") from e
    if error:
        raise SlurmError(f"Can't retrieve SLURM information: {error}")
    return output


def parse_cpu_used(sinfo_output: str) -> float:
    cpu_info_split = sinfo_output.split("/")
    cpu_used_count = int(cpu_info_split[0])
    cpu_inactive_count = int(cpu_info_split[1])
    return 100 * cpu_used_count / (cpu_used_count + cpu_inactive_count)


def parse_cpu_load(sinfo_output: str) -> float:
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
    # allocated cpus
    sinfo_cpus_used = execute_command(
        ssh_config,
        ["sinfo", "--partition", partition, "-O", "NodeAIOT", "--noheader"],
    )
    allocated_cpus = parse_cpu_used(sinfo_cpus_used)
    # cluster load
    sinfo_cpus_load = execute_command(
        ssh_config,
        [
            "sinfo",
            "--partition",
            partition,
            "-N",
            "-O",
            "CPUsLoad,CPUs",
            "--noheader",
        ],
    )
    cluster_load = parse_cpu_load(sinfo_cpus_load)
    # queued jobs
    queued_jobs = int(
        execute_command(
            ssh_config,
            [
                "squeue",
                "--partition",
                partition,
                "--noheader",
                "-t",
                "pending",
                "|",
                "wc",
                "-l",
            ],
        )
    )
    return allocated_cpus, cluster_load, queued_jobs
