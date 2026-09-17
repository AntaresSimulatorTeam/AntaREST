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

ASSETS_PATH = Path(__file__).parent / "assets"


def check_legacy_gems_taxonomy_integrity(taxonomy: GemsTaxonomy) -> None:
    assert taxonomy is not None
    assert taxonomy.id == "antares_legacy_taxonomy"
    assert taxonomy.description == "GEMS taxonomy configuration for Antares Legacy Models."
    assert len(taxonomy.categories) == 15

    categories_by_id = {c.id: c for c in taxonomy.categories}

    balance = categories_by_id["balance"]
    assert balance.id == "balance"
    assert balance.parent_category is None
    assert balance.variables == [{"id": "unsupplied_energy"}, {"id": "spilled_energy"}]
    assert balance.ports == [{"id": "balance_port"}]
    assert balance.binding_constraints == [{"id": "balance"}]
    assert balance.extra_outputs is not None
    assert len(balance.extra_outputs) == 5

    generation = categories_by_id["generation"]
    assert generation.id == "generation"
    assert generation.parent_category is None
    assert generation.ports == [{"id": "balance_port"}]

    dispatchable = categories_by_id["dispatchable_generation"]
    assert dispatchable.id == "dispatchable_generation"
    assert dispatchable.parent_category == "generation"
    assert dispatchable.variables == [{"id": "generation_power"}]
    assert dispatchable.properties == [{"id": "technology"}]


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
    check_legacy_gems_taxonomy_integrity(saved_taxonomy)
