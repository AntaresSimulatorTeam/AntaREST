from abc import abstractmethod
from enum import Enum
from typing import Optional, Any, List
from antarest.core.custom_types import JSON


class CacheConstants(Enum):
    RAW_STUDY = "RAW_STUDY"
    STUDY_FACTORY = "STUDY_FACTORY"


class ICache:
    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def put(self, id: str, data: Any, timeout: int = 600000) -> None:
        pass

    @abstractmethod
    def get(self, id: str, refresh_timeout: Optional[int] = None) -> Any:
        pass

    @abstractmethod
    def invalidate(self, id: str) -> None:
        pass

    @abstractmethod
    def invalidate_all(self, ids: List[str]) -> None:
        pass
