from abc import abstractmethod
from typing import Optional, List
from antarest.core.custom_types import JSON


class ICache:
    @abstractmethod
    def start(self):
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
