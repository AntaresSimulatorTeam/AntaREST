from enum import Enum

from dataclasses import dataclass

from antarest.common.custom_types import JSON


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

    def to_dict(self) -> JSON:
        return {
            "status": str(self.execution_status),
            "msg": self.msg,
            "exit_code": self.exit_code,
        }
