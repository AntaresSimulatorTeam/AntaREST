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

from http import HTTPStatus
from http.client import HTTPException
from pathlib import Path

from antares.study.version.exceptions import ApplicationError
from antares.study.version.model.study_version import StudyVersion
from antares.study.version.upgrade_app import UpgradeApp

from antarest.core.exceptions import UnsupportedStudyVersion
from antarest.study.model import (
    STUDY_VERSION_7_0,
    STUDY_VERSION_7_1,
    STUDY_VERSION_7_2,
    STUDY_VERSION_8,
    STUDY_VERSION_8_1,
    STUDY_VERSION_8_2,
    STUDY_VERSION_8_3,
    STUDY_VERSION_8_4,
    STUDY_VERSION_8_5,
    STUDY_VERSION_8_6,
    STUDY_VERSION_8_7,
    STUDY_VERSION_8_8,
    STUDY_VERSION_9_2,
    STUDY_VERSION_9_3,
)

AVAILABLE_VERSIONS = [
    STUDY_VERSION_7_0,
    STUDY_VERSION_7_1,
    STUDY_VERSION_7_2,
    STUDY_VERSION_8,
    STUDY_VERSION_8_1,
    STUDY_VERSION_8_2,
    STUDY_VERSION_8_3,
    STUDY_VERSION_8_4,
    STUDY_VERSION_8_5,
    STUDY_VERSION_8_6,
    STUDY_VERSION_8_7,
    STUDY_VERSION_8_8,
    STUDY_VERSION_9_2,
    STUDY_VERSION_9_3,
]


class InvalidUpgrade(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.UNPROCESSABLE_ENTITY, message)


class StudyUpgrader:
    def __init__(self, study_path: Path, target_version: StudyVersion):
        self.app = UpgradeApp(study_path, version=target_version)

    def upgrade(self) -> None:
        try:
            self.app()
        except ApplicationError as e:
            raise InvalidUpgrade(str(e)) from e

    def should_denormalize_study(self) -> bool:
        return self.app.should_denormalize


def _get_version_index(version: StudyVersion) -> int:
    try:
        return AVAILABLE_VERSIONS.index(version)
    except ValueError:
        available_versions = [f"{v:2d}" for v in AVAILABLE_VERSIONS]
        raise UnsupportedStudyVersion(f"Version '{version}' isn't among supported versions: {available_versions}")


def find_next_version(from_version: StudyVersion) -> StudyVersion:
    """
    Find the next study version from the given version.

    Args:
        from_version: The current version as a string.

    Returns:
        The next version as a string.

    Raises:
        UnsupportedStudyVersion if the current version is not supported or if the study is already in last version.
    """
    start_pos = _get_version_index(from_version)
    if start_pos == len(AVAILABLE_VERSIONS) - 1:
        raise UnsupportedStudyVersion(f"Your study is already in the latest supported version: '{from_version}'")
    return AVAILABLE_VERSIONS[start_pos + 1]


def check_versions_coherence(from_version: StudyVersion, target_version: StudyVersion) -> None:
    start_pos = _get_version_index(from_version)
    final_pos = _get_version_index(target_version)
    if final_pos == start_pos:
        raise InvalidUpgrade(f"Your study is already in the version you asked: {from_version}")
    elif final_pos < start_pos:
        raise InvalidUpgrade(f"Cannot downgrade your study version : from {from_version} to {target_version}")
