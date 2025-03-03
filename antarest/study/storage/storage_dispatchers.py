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

"""
This module provides the ``StudyStorageService`` class, which acts as a dispatcher for study storage services.
It determines the appropriate study storage service based on the type of study provided.
"""

from pathlib import Path
from typing import BinaryIO, Optional

from typing_extensions import override

from antarest.study.model import RawStudy, Study, StudySimResultDTO
from antarest.study.storage.output_storage import IOutputStorage
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy
from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService


class OutputStorageDispatcher(IOutputStorage):
    def __init__(self, raw_study_service: RawStudyService, variant_study_service: VariantStudyService) -> None:
        self.raw_study_service = raw_study_service
        self.variant_study_service = variant_study_service

    def _get_storage(self, study: Study) -> IOutputStorage:
        """
        Get the appropriate study storage service based on the type of study.

        Args:
            study: The study object for which the storage service is required.

        Returns:
            The study storage service associated with the study type.
        """
        match study:
            case RawStudy():
                return self.raw_study_service
            case VariantStudy():
                return self.variant_study_service
            case _:
                raise NotImplementedError(f"The study type {type(study)} is not supported")

    @override
    def import_output(
        self,
        study: Study,
        output: BinaryIO | Path,
        output_name: Optional[str] = None,
    ) -> Optional[str]:
        return self._get_storage(study).import_output(study, output, output_name)

    @override
    def get_study_sim_result(self, metadata: Study) -> list[StudySimResultDTO]:
        return self._get_storage(metadata).get_study_sim_result(metadata)

    @override
    def delete_output(self, metadata: Study, output_id: str) -> None:
        self._get_storage(metadata).delete_output(metadata, output_id)

    @override
    def export_output(self, metadata: Study, output_id: str, target: Path) -> None:
        self._get_storage(metadata).export_output(metadata, output_id, target)

    @override
    def archive_study_output(self, study: Study, output_id: str) -> bool:
        return self._get_storage(study).archive_study_output(study, output_id)

    @override
    def unarchive_study_output(self, study: Study, output_id: str, keep_src_zip: bool) -> bool:
        return self._get_storage(study).unarchive_study_output(study, output_id, keep_src_zip)

    @override
    def get_output_path(self, study: Study, output_id: str) -> Path:
        return self._get_storage(study).get_output_path(study, output_id)
