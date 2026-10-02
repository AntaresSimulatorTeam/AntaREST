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

from antarest.core.exceptions import GemsTaxonomyAlreadyExists
from antarest.study.business.model.gems.taxonomy import GemsTaxonomy
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.rawstudy.model.filesystem.yaml_file_node import YAMLReader
from tests.study.dao.conftest import check_gems_taxonomy_integrity

ASSETS_PATH = Path(__file__).parent / "assets"


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
def test_nominal_cases(dao_10_2: StudyDao) -> None:
    dao = dao_10_2

    # First ensure there is no taxonomy in the study
    assert dao.get_taxonomy() is None

    # Saves a taxonomy
    gems_taxonomy_asset_path = ASSETS_PATH / "gems" / "taxonomy" / "taxonomy.yml"
    content = YAMLReader().read(gems_taxonomy_asset_path)["taxonomy"]
    taxonomy = GemsTaxonomy.model_validate(content)
    dao.save_taxonomy(taxonomy)

    # Ensures we cannot replace a taxonomy once it already exists in a study
    with pytest.raises(GemsTaxonomyAlreadyExists):
        dao.save_taxonomy(taxonomy)

    # Fetch the saved taxonomy and check its content
    saved_taxonomy = dao.get_taxonomy()
    assert saved_taxonomy is not None
    check_gems_taxonomy_integrity(saved_taxonomy)
