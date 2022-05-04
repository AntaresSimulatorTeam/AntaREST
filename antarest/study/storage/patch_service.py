from pathlib import Path
from typing import Union, Optional

from pydantic import ValidationError

from antarest.study.model import Patch, PatchOutputs, RawStudy
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.dbmodel import (
    VariantStudy,
)


class PatchService:
    def __init__(self, repository: Optional[StudyMetadataRepository] = None):
        self.repository = repository

    def get(
        self, study: Union[RawStudy, VariantStudy], get_from_file: bool = False
    ) -> Patch:
        patch = Patch()

        if not get_from_file:
            try:
                patch = Patch.parse_raw(study.additional_data.patch)
            except (AttributeError, ValidationError):
                get_from_file = True

        if get_from_file:
            patch_path = (Path(study.path)) / "patch.json"
            if patch_path.exists():
                patch = Patch.parse_file(patch_path)

        return patch

    def get_from_filestudy(self, file_study: FileStudy) -> Patch:
        patch = Patch()
        patch_path = (Path(file_study.config.study_path)) / "patch.json"
        if patch_path.exists():
            patch = Patch.parse_file(patch_path)
        return patch

    def set_reference_output(
        self,
        study: Union[RawStudy, VariantStudy],
        output_id: str,
        status: bool = True,
    ) -> None:
        patch = self.get(study)
        if patch.outputs is not None:
            patch.outputs.reference = output_id if status else None
        elif status:
            patch.outputs = PatchOutputs(reference=output_id)
        self.save(study, patch)

    def save(self, study: Union[RawStudy, VariantStudy], patch: Patch) -> None:
        if self.repository:
            study.additional_data.patch = patch.json()
            self.repository.save(study)

        patch_content = patch.json()
        patch_path = (Path(study.path)) / "patch.json"
        patch_path.write_text(patch_content)
