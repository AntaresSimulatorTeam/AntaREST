from abc import ABC, abstractmethod
from typing import List, Optional, Dict, TypeVar, Generic, Any, Union

from antarest.common.custom_types import JSON, SUB_JSON
from antarest.storage_api.filesystem.config.model import Config

G = TypeVar("G")
S = TypeVar("S")
V = TypeVar("V")


class INode(ABC, Generic[G, S, V]):
    @abstractmethod
    def build(self, config: Config) -> "TREE":
        pass

    @abstractmethod
    def get(self, url: Optional[List[str]] = None, depth: int = -1) -> G:
        pass

    @abstractmethod
    def save(self, data: S, url: Optional[List[str]] = None) -> None:
        pass

    @abstractmethod
    def validate(self, data: V) -> None:
        pass


TREE = Dict[str, INode[Any, Any, Any]]
