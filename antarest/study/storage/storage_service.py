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

from typing import Union

from antarest.study.common.outputstorage import IOutputStorageService
from antarest.study.common.studystorage import IStudyStorageService
from antarest.study.model import RawStudy, Study
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy
from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService


class StudyStorageService:
    """
    A class that acts as a dispatcher for study storage services.

    This class determines the appropriate study storage service based on the type of study provided.
    It delegates the study storage operations to the corresponding service.

    Attributes:
        raw_study_service: The service for managing raw studies.
        variant_study_service: The service for managing variant studies.
    """

    def __init__(
        self,
        raw_study_service: RawStudyService,
        variant_study_service: VariantStudyService,
    ):
        """
        Initialize the ``StudyStorageService`` with raw and variant study services.

        Args:
            raw_study_service: The service for managing raw studies.
            variant_study_service: The service for managing variant studies.
        """
        self.raw_study_service = raw_study_service
        self.variant_study_service = variant_study_service

    def get_storage(self, study: Study) -> IStudyStorageService[Union[RawStudy, VariantStudy]]:
        """
        Get the appropriate study storage service based on the type of study.

        Args:
            study: The study object for which the storage service is required.

        Returns:
            The study storage service associated with the study type.
        """
        return self.raw_study_service if isinstance(study, RawStudy) else self.variant_study_service


class OutputStorageService:
    """
    A class that acts as a dispatcher for output storage services.

    This class determines the appropriate output storage service based on the type of study provided.
    It delegates the output storage operations to the corresponding service.

    Attributes:
        raw_study_service: The service for managing raw studies.
        variant_study_service: The service for managing variant studies.
    """

    def __init__(
        self,
        raw_study_service: RawStudyService,
        variant_study_service: VariantStudyService,
    ):
        """
        Initialize the ``OutputStorageService`` with raw and variant study services.

        Args:
            raw_study_service: The service for managing raw studies.
            variant_study_service: The service for managing variant studies.
        """
        self.raw_study_service = raw_study_service
        self.variant_study_service = variant_study_service

    def get_storage(self, study: Study) -> IOutputStorageService[Union[RawStudy, VariantStudy]]:
        """
        Get the appropriate study storage service based on the type of study.

        Args:
            study: The study object for which the storage service is required.

        Returns:
            The study storage service associated with the study type.
        """
        return self.raw_study_service if isinstance(study, RawStudy) else self.variant_study_service
