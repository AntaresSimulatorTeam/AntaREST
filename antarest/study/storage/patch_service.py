# Copyright (c) 2025, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import typing as t
from pathlib import Path

from antarest.core.serde.json import from_json
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
                return Patch.model_validate(from_json(study.additional_data.patch))

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
            study.additional_data.patch = patch.model_dump_json()
            self.repository.save(study)

        patch_path = (Path(study.path)) / PATCH_JSON
        patch_path.parent.mkdir(parents=True, exist_ok=True)
        patch_path.write_text(patch.model_dump_json())
