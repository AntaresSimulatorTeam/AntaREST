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

from http import HTTPStatus
from http.client import HTTPException
from pathlib import Path

from antares.study.version.exceptions import ApplicationError
from antares.study.version.model.study_version import StudyVersion
from antares.study.version.upgrade_app import UpgradeApp

from antarest.core.exceptions import UnsupportedStudyVersion

AVAILABLE_VERSIONS = ["700", "710", "720", "800", "810", "820", "830", "840", "850", "860", "870", "880", "920"]


class InvalidUpgrade(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.UNPROCESSABLE_ENTITY, message)


class StudyUpgrader:
    def __init__(self, study_path: Path, target_version: str):
        try:
            version = StudyVersion.parse(target_version)
        except ValueError as e:
            raise InvalidUpgrade(str(e)) from e
        else:
            self.app = UpgradeApp(study_path, version=version)

    def upgrade(self) -> None:
        try:
            self.app()
        except ApplicationError as e:
            raise InvalidUpgrade(str(e)) from e

    def should_denormalize_study(self) -> bool:
        return self.app.should_denormalize


def _get_version_index(version: str) -> int:
    try:
        return AVAILABLE_VERSIONS.index(version)
    except ValueError:
        raise UnsupportedStudyVersion(f"Version '{version}' isn't among supported versions: {AVAILABLE_VERSIONS}")


def find_next_version(from_version: str) -> str:
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


def check_versions_coherence(from_version: str, target_version: str) -> None:
    start_pos = _get_version_index(from_version)
    final_pos = _get_version_index(target_version)
    if final_pos == start_pos:
        raise InvalidUpgrade(f"Your study is already in the version you asked: {from_version}")
    elif final_pos < start_pos:
        raise InvalidUpgrade(f"Cannot downgrade your study version : from {from_version} to {target_version}")
