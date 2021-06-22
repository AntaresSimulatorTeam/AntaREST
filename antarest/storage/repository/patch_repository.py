from pathlib import Path

from antarest.storage.model import Patch, RawStudy


class PatchRepository:
    def get(self, study: RawStudy) -> Patch:
        patch_path = Path(study.path) / "patch.json"
        return Patch.parse_file(patch_path)

    def save(self, study: RawStudy, patch: Patch) -> None:
        patch_content = patch.json()
        patch_path = Path(study.path) / "patch.json"
        patch_path.write_text(patch_content)

    def patch(self, study: RawStudy, new_patch: Patch) -> None:
        old_patch = self.get(study)
        merged_path = old_patch.patch(new_patch)
        self.save(study, merged_path)
