from enum import Enum

from dataclasses import dataclass


class ExecutionStatus(Enum):
    PENDING = "pending"
    FAILED = "failed"
    SUCCESS = "success"
    RUNNING = "running"


@dataclass
class ExecutionResult:
    execution_status: ExecutionStatus
    msg: str
    exit_code: int
