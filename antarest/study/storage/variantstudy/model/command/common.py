from dataclasses import dataclass


@dataclass
class CommandOutput:
    status: bool
    message: str
