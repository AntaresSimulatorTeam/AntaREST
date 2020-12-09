from abc import ABC, abstractmethod
from typing import List, Optional, Dict, TypeVar, Generic, Any, Union

from api_iso_antares.custom_types import JSON, SUB_JSON

T = TypeVar("T")


class INode(ABC, Generic[T]):
    @abstractmethod
    def get(self, url: Optional[List[str]] = None) -> T:
        pass

    @abstractmethod
    def save(self, data: T, url: Optional[List[str]] = None) -> None:
        pass

    @abstractmethod
    def validate(self, data: T) -> None:
        pass


TREE = Dict[str, INode[Any]]
