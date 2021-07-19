from antarest.core.custom_types import JSON
from antarest.storage.model import Patch, PatchOutputs, RawStudy
from antarest.storage.repository.patch_repository import PatchRepository


class PatchService:
    def __init__(self, repository: PatchRepository) -> None:
        self.repository: PatchRepository = repository

    def get(self, study: RawStudy) -> Patch:
        return self.repository.get(study)

    def set_reference_output(
        self, study: RawStudy, output_id: str, status: bool = True
    ) -> None:
        patch = self.repository.get(study)
        if patch.outputs is not None:
            patch.outputs.reference = output_id if status else None
        elif status:
            patch.outputs = PatchOutputs(reference=output_id)
        self.repository.save(study, patch)

    def patch(self, study: RawStudy, new_patch_content: JSON) -> None:
        new_patch = Patch.parse_obj(new_patch_content)
        self.repository.patch(study, new_patch)
