from typing import TYPE_CHECKING, Any, Dict, Sequence

from antarest.study.interface.study_interface import StudyInterface, StudyInterfaceFactory

if TYPE_CHECKING:
    from antarest.study.service import StudyService

from antarest.study.storage.rawstudy.model.filesystem.config.area import UIProperties
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


def _get_ui_info_map(file_study: FileStudy, area_ids: Sequence[str]) -> Dict[str, Any]:
    """
    Get the UI information (a JSON object) for each selected Area.

    Args:
        file_study: A file study from which the configuration can be read.
        area_ids: List of selected area IDs.

    Returns:
        Dictionary where keys are IDs, and values are UI objects.

    Raises:
        ChildNotFoundError: if one of the Area IDs is not found in the configuration.
    """
    # If there is no ID, it is better to return an empty dictionary
    # instead of raising an obscure exception.
    if not area_ids:
        return {}

    ui_info_map = file_study.tree.get(["input", "areas", ",".join(area_ids), "ui"])

    # If there is only one ID in the `area_ids`, the result returned from
    # the `file_study.tree.get` call will be a single UI object.
    # On the other hand, if there are multiple values in `area_ids`,
    # the result will be a dictionary where the keys are the IDs,
    # and the values are the corresponding UI objects.
    if len(area_ids) == 1:
        ui_info_map = {area_ids[0]: ui_info_map}

    # Convert to UIProperties to ensure that the UI object is valid.
    ui_info_map = {area_id: UIProperties(**ui_info).to_config() for area_id, ui_info in ui_info_map.items()}

    return ui_info_map


class FileStudyInterface(StudyInterface):
    """
    Implementation which fetches and writes study data from file tree representation.
    """

    def __init__(self, file_study: FileStudy):
        self._file_study = file_study

    def get_all_areas_ui_info(self) -> Dict[str, Any]:
        """
        Retrieve information about all areas' user interface (UI) from the study.

        Args:
            study: The raw study object containing the study's data.

        Returns:
            A dictionary containing information about the user interface for the areas.

        Raises:
            ChildNotFoundError: if one of the Area IDs is not found in the configuration.
        """
        study = self._file_study
        area_ids = list(study.config.areas)
        res = _get_ui_info_map(study, area_ids)
        return res


class FileStudyInterfaceFactory(StudyInterfaceFactory):
    def __init__(self, study_service: "StudyService"):
        self._study_service = study_service

    def create(self, study_id: str) -> StudyInterface:
        study_metadata = self._study_service.get_study(study_id)
        file_study = self._study_service.storage_service.get_storage(study_metadata).get_raw(study_metadata)
        return FileStudyInterface(file_study)
