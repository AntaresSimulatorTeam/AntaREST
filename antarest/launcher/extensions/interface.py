from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Any

from antarest.core.model import JSON


class ILauncherExtension(ABC):
    @abstractmethod
    def get_name(self) -> str:
        raise NotImplementedError()

    @abstractmethod
    def after_export_flat_hook(
        self,
        job_id: str,
        study_id: str,
        study_export_path: Path,
        ext_opts: Any,
    ) -> None:
        pass
