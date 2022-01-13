from pathlib import Path
from typing import Union

from antarest.core.model import JSON
from antarest.study.model import Patch, PatchOutputs, RawStudy
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.dbmodel import (
    VariantStudy,
)


class PatchService:
    def get(self, study: Union[RawStudy, VariantStudy, FileStudy]) -> Patch:
        patch_path = (
            Path(study.path)
            if not isinstance(study, FileStudy)
            else study.config.study_path
        ) / "patch.json"
        if patch_path.exists():
            return Patch.parse_file(patch_path)
        return Patch()

    def set_reference_output(
        self,
        study: Union[RawStudy, VariantStudy, FileStudy],
        output_id: str,
        status: bool = True,
    ) -> None:
        patch = self.get(study)
        if patch.outputs is not None:
            patch.outputs.reference = output_id if status else None
        elif status:
            patch.outputs = PatchOutputs(reference=output_id)
        self.save(study, patch)

    def save(
        self, study: Union[RawStudy, VariantStudy, FileStudy], patch: Patch
    ) -> None:
        patch_content = patch.json()
        patch_path = (
            Path(study.path)
            if not isinstance(study, FileStudy)
            else study.config.study_path
        ) / "patch.json"
        patch_path.write_text(patch_content)
