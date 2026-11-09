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
from pathlib import Path

import pytest

from antarest.core.exceptions import GemsLibraryAlreadyExists, GemsTaxonomyNotFound
from antarest.study.business.model.gems.library import GemsLibrary
from antarest.study.business.model.gems.taxonomy import GemsTaxonomy
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.rawstudy.model.filesystem.yaml_file_node import YAMLReader
from tests.study.dao.conftest import check_8_1_gems_library_integrity

ASSETS_PATH = Path(__file__).parent / "assets"


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
def test_nominal_cases(dao_10_2: StudyDao) -> None:
    dao = dao_10_2

    # First ensure there is no library in the study
    assert dao.get_library() is None

    # Saves a library
    gems_library_asset_path = ASSETS_PATH / "gems" / "libraries" / "8_1_simulator_nr_tests.yml"
    content = YAMLReader().read(gems_library_asset_path)["library"]
    library = GemsLibrary.model_validate(content)
    dao.save_library(library)

    # Ensures we cannot replace a library once it already exists in a study
    with pytest.raises(GemsLibraryAlreadyExists):
        dao.save_library(library)

    # Fetch the saved library and check its content
    saved_library = dao.get_library()
    assert saved_library is not None
    check_8_1_gems_library_integrity(saved_library)


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
def test_taxonomy_foreign_keys(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
    assert dao.get_library() is None

    # First save a taxonomy
    gems_taxonomy_asset_path = ASSETS_PATH / "gems" / "taxonomy" / "taxonomy.yml"
    content = YAMLReader().read(gems_taxonomy_asset_path)["taxonomy"]
    taxonomy = GemsTaxonomy.model_validate(content)
    dao.save_taxonomy(taxonomy)

    # Create a Library that references a fake taxonomy -> Should fail
    library = GemsLibrary(id="library", taxonomy="fake taxonomy")
    with pytest.raises(GemsTaxonomyNotFound, match="Taxonomy 'fake taxonomy' not found inside study"):
        dao.save_library(library)

    # Create a Library referencing the righ taxonomy -> Should succeed
    library = GemsLibrary(id="library", taxonomy=taxonomy.id)
    dao.save_library(library)
