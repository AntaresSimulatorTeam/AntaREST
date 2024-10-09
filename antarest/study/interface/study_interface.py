from abc import ABC, abstractmethod
from typing import Any, Dict


class StudyInterface(ABC):
    """
    Interface to access and mofify study data.
    """

    @abstractmethod
    def get_all_areas_ui_info(self) -> Dict[str, Any]:
        raise NotImplementedError()


class StudyInterfaceFactory(ABC):
    @abstractmethod
    def create(self, study_id: str) -> StudyInterface:
        raise NotImplementedError()
