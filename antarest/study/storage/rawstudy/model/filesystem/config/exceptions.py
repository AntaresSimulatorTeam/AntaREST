from pathlib import Path
from typing import cast


class BaseConfigError(Exception):
    """Base class of the configuration errors."""


class SimulationParsingError(BaseConfigError):
    def __init__(self, output_path: Path, reason: str):
        super().__init__(output_path, reason)

    @property
    def output_path(self) -> Path:
        return cast(Path, self.args[0])

    @property
    def reason(self) -> str:
        return cast(str, self.args[1])

    def __str__(self) -> str:
        output_path = self.output_path
        reason = self.reason
        return f"Fail to parse the simulation file '{output_path}': {reason}"


class XpansionParsingError(BaseConfigError):
    def __init__(self, xpansion_json: Path, reason: str):
        super().__init__(xpansion_json, reason)

    @property
    def xpansion_json(self) -> Path:
        return cast(Path, self.args[0])

    @property
    def reason(self) -> str:
        return cast(str, self.args[1])

    def __str__(self) -> str:
        xpansion_json = self.xpansion_json
        reason = self.reason
        return f"Fail to parse the Xpansion file '{xpansion_json}': {reason}"
