import json
import typing as t
from pathlib import Path

from antarest.study.model import Patch, PatchOutputs, RawStudy, StudyAdditionalData
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy

PATCH_JSON = "patch.json"


class PatchService:
    """
    Handle patch file ("patch.json") for a RawStudy or VariantStudy
    """

    def __init__(self, repository: t.Optional[StudyMetadataRepository] = None):
        self.repository = repository

    def get(self, study: t.Union[RawStudy, VariantStudy], get_from_file: bool = False) -> Patch:
        if not get_from_file and study.additional_data is not None:
            # the `study.additional_data.patch` field is optional
            if study.additional_data.patch:
                patch_obj = json.loads(study.additional_data.patch or "{}")
                return Patch.parse_obj(patch_obj)

        patch = Patch()
        patch_path = Path(study.path) / PATCH_JSON
        if patch_path.exists():
            patch = Patch.parse_file(patch_path)

        return patch

    def get_from_filestudy(self, file_study: FileStudy) -> Patch:
        patch = Patch()
        patch_path = (Path(file_study.config.study_path)) / PATCH_JSON
        if patch_path.exists():
            patch = Patch.parse_file(patch_path)
        return patch

    def set_reference_output(
        self,
        study: t.Union[RawStudy, VariantStudy],
        output_id: str,
        status: bool = True,
    ) -> None:
        patch = self.get(study)
        if patch.outputs is not None:
            patch.outputs.reference = output_id if status else None
        elif status:
            patch.outputs = PatchOutputs(reference=output_id)
        self.save(study, patch)

    def save(self, study: t.Union[RawStudy, VariantStudy], patch: Patch) -> None:
        if self.repository:
            study.additional_data = study.additional_data or StudyAdditionalData()
            study.additional_data.patch = patch.json()
            self.repository.save(study)

        patch_path = (Path(study.path)) / PATCH_JSON
        patch_path.parent.mkdir(parents=True, exist_ok=True)
        patch_path.write_text(patch.json())
