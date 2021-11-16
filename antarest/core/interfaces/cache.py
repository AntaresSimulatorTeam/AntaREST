from abc import abstractmethod
from enum import Enum
from typing import Optional, List

from antarest.core.model import JSON


class CacheConstants(Enum):
    RAW_STUDY = "RAW_STUDY"
    STUDY_FACTORY = "STUDY_FACTORY"
    STUDY_LISTING_SUMMARY = "STUDY_LISTING_SUMMARY"
    STUDY_LISTING = "STUDY_LISTING"


class ICache:
    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def put(self, id: str, data: JSON, timeout: int = 600000) -> None:
        pass

    @abstractmethod
    def get(
        self, id: str, refresh_timeout: Optional[int] = None
    ) -> Optional[JSON]:
        pass

    @abstractmethod
    def invalidate(self, id: str) -> None:
        pass

    @abstractmethod
    def invalidate_all(self, ids: List[str]) -> None:
        pass
