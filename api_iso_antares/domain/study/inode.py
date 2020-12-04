from abc import ABC, abstractmethod
from typing import List, Optional, Dict

from api_iso_antares.custom_types import JSON, SUB_JSON


class INode(ABC):
    @abstractmethod
    def get(self, url: List[str]) -> SUB_JSON:
        pass

    @abstractmethod
    def to_json(self) -> SUB_JSON:
        pass

    @abstractmethod
    def validate(self, data: JSON):
        pass


TREE = Dict[str, INode]
