from abc import ABC, abstractmethod
from typing import List, Optional, Dict, TypeVar, Generic, Any, Union

from antarest.common.custom_types import JSON, SUB_JSON
from antarest.storage.repository.filesystem.config.model import StudyConfig

G = TypeVar("G")
S = TypeVar("S")
V = TypeVar("V")


class INode(ABC, Generic[G, S, V]):
    @abstractmethod
    def build(self, config: StudyConfig) -> "TREE":
        pass

    @abstractmethod
    def get(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
    ) -> G:
        pass

    @abstractmethod
    def save(self, data: S, url: Optional[List[str]] = None) -> None:
        pass

    @abstractmethod
    def check_errors(
        self, data: V, url: Optional[List[str]] = None, raising: bool = False
    ) -> List[str]:
        pass

    def _assert_url(self, url: Optional[List[str]] = None) -> None:
        url = url or []
        if len(url) > 0:
            raise ValueError(
                f"url should be fully resolved when arrives on {self.__class__.__name__}"
            )


TREE = Dict[str, INode[Any, Any, Any]]
