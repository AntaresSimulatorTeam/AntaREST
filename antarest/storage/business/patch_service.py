from antarest.common.custom_types import JSON
from antarest.common.requests import RequestParameters
from antarest.storage.model import Patch, PatchOutputs
from antarest.storage.repository.patch_repository import PatchRepository
from antarest.storage.service import StorageService


class PatchService:
    def __init__(
        self, repository: PatchRepository, storage_service: StorageService
    ) -> None:
        self.repository: PatchRepository = repository
        self.storage_service: StorageService = storage_service

    def get(self, study_id: str, params: RequestParameters) -> Patch:
        study = self.storage_service.get_raw_study(study_id, params)
        return self.repository.get(study)

    def set_reference_output(
        self, study_id: str, output_id: str, params: RequestParameters
    ) -> None:
        study = self.storage_service.get_raw_study(study_id, params)
        patch = self.repository.get(study)
        if patch.outputs is not None:
            patch.outputs.reference = output_id
        else:
            patch.outputs = PatchOutputs(reference=output_id)
        self.repository.save(study, patch)

    def patch(
        self, study_id: str, new_patch_content: JSON, params: RequestParameters
    ) -> None:
        study = self.storage_service.get_raw_study(study_id, params)
        new_patch = Patch.parse_obj(new_patch_content)
        self.repository.patch(study, new_patch)
