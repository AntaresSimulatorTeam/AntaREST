# Copyright (c) 2026, RTE (https://www.rte-france.com)
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
Adapts other packages components to provide the necessary interface for the output service.
"""

from pathlib import Path

from typing_extensions import override

from antarest.core.config import DEFAULT_WORKSPACE_NAME
from antarest.core.model import StudyPermissionType
from antarest.output.output_service import IStudyMetadataProvider, StudyMetadata
from antarest.output.storage.file.file_output_storage import FileStudyOutputs, IFileOutputsProvider
from antarest.study.service import StudyService
from antarest.study.storage.utils import assert_permission


def study_service_as_file_outputs_provider(study_service: StudyService) -> IFileOutputsProvider:
    """
    Adapts a study service to provide only the necessary functionalities to the file output storage.
    """

    class StudyServiceAdapter(IFileOutputsProvider):
        @override
        def get_outputs(self, study_id: str) -> FileStudyOutputs:
            metadata = study_service.get_study(study_id)
            return FileStudyOutputs(
                get_file_study=lambda: study_service.get_file_study(metadata),
                outputs_path=Path(metadata.path) / "output",
                study_workspace=getattr(metadata, "workspace", DEFAULT_WORKSPACE_NAME),
            )

    return StudyServiceAdapter()


def study_service_as_studies_repository(study_service: StudyService) -> IStudyMetadataProvider:
    """
    Adapts a study service to provide only the necessary functionalities to the output service.
    """

    class StudyServiceAdapter(IStudyMetadataProvider):
        @override
        def get_study_metadata(self, study_id: str) -> StudyMetadata:
            study = study_service.get_study(study_id)
            return StudyMetadata(id=study.id, name=study.name or "<Unnamed study>")

        @override
        def assert_permission(self, study_id: str, permission: StudyPermissionType) -> None:
            study = study_service.get_study(study_id)
            assert_permission(study, StudyPermissionType.READ)
            study_service.assert_study_unarchived(study)

    return StudyServiceAdapter()
