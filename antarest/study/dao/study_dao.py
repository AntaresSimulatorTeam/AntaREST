from abc import ABC, abstractmethod
from typing import Any, Dict


class StudyDAO(ABC):
    """
    Interface to access and mofify study data.
    """

    @abstractmethod
    def get_all_areas_ui_info(self) -> Dict[str, Any]:
        raise NotImplementedError()


class StudiesDAO(ABC):
    @abstractmethod
    def get_study(self, study_id: str) -> StudyDAO:
        raise NotImplementedError()
