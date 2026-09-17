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
import shutil
from pathlib import Path

from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao
from tests.study.dao.test_database_gems_taxonomy_dao import check_legacy_gems_taxonomy_integrity

ASSETS_PATH = Path(__file__).parent.parent / "assets"


def test_default_case(dao_10_2: StudyDao) -> None:
    # We should not have a taxonomy for default studies
    taxonomy = dao_10_2.get_taxonomy()
    assert taxonomy is None


def test_taxonomy_roundtrip(filestudy_dao_v10_2: FileStudyTreeDao) -> None:
    dao = filestudy_dao_v10_2
    tax_folder = dao.get_file_study().config.study_path / "input"
    tax_folder.mkdir(exist_ok=True)
    shutil.copy(ASSETS_PATH / "gems" / "taxonomy" / "taxonomy.yml", tax_folder / "taxonomy.yml")

    taxonomy = dao.get_taxonomy()
    assert taxonomy is not None
    check_legacy_gems_taxonomy_integrity(taxonomy)

    # Remove the taxonomy file
    (tax_folder / "taxonomy.yml").unlink()
    assert dao.get_taxonomy() is None

    # Save the old content
    dao.save_taxonomy(taxonomy)
    taxonomy = dao.get_taxonomy()
    assert taxonomy is not None
    check_legacy_gems_taxonomy_integrity(taxonomy)
