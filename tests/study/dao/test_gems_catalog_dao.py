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
from pydantic import ValidationError

from antarest.core.exceptions import GemsCatalogAlreadyExists
from antarest.study.business.model.gems.catalog import GemsCatalog
from antarest.study.dao.api.study_dao import ReadOnlyAdapter, StudyDao
from antarest.study.storage.rawstudy.model.filesystem.yaml_file_node import YAMLReader
from tests.study.dao.conftest import assert_catalogs_equal, prepare_catalog_taxonomy

ASSET = Path(__file__).parent / "assets/gems/catalogs/antares_legacy_area_catalog.yml"


def test_catalogs_roundtrip(dao_10_2: StudyDao, gems_catalog: GemsCatalog) -> None:
    prepare_catalog_taxonomy(dao_10_2)
    assert dao_10_2.get_catalogs() == []
    # The fixture comes from AntaresLegacyModels-to-GEMS-Converter.
    expected = YAMLReader().read(ASSET)["catalog"]
    dao_10_2.save_catalogs([gems_catalog])
    saved = dao_10_2.get_catalogs()
    assert len(saved) == 1
    actual = saved[0].model_dump(mode="json", by_alias=True, exclude_unset=True)
    actual["metrics-definition"].sort(key=lambda metric: metric["id"])
    expected["metrics-definition"].sort(key=lambda metric: metric["id"])
    assert actual == expected
    assert ReadOnlyAdapter(dao_10_2).get_catalogs() == saved

    other = gems_catalog.model_copy(update={"id": "another_catalog"})
    dao_10_2.save_catalogs([other])
    assert_catalogs_equal(dao_10_2.get_catalogs(), [other, gems_catalog])

    with pytest.raises(GemsCatalogAlreadyExists):
        dao_10_2.save_catalogs([gems_catalog.model_copy(update={"taxonomy": "another_taxonomy"})])
    assert_catalogs_equal(dao_10_2.get_catalogs(), [other, gems_catalog])


def test_duplicate_metric_ids_are_rejected() -> None:
    content = YAMLReader().read(ASSET)["catalog"]
    # A different definition with the same ID would make view references ambiguous.
    content["metrics-definition"][1]["id"] = content["metrics-definition"][0]["id"]
    with pytest.raises(ValidationError, match="Duplicate metric IDs in catalog: OV.COST"):
        GemsCatalog.model_validate(content)


@pytest.mark.parametrize("field", ["terms-operator", "time-operator"])
def test_invalid_operator(field: str) -> None:
    content = YAMLReader().read(ASSET)["catalog"]
    content["metrics-definition"][0][field] = "unsupported"
    with pytest.raises(ValidationError, match=field):
        GemsCatalog.model_validate(content)


@pytest.mark.parametrize("catalog_id", ["../outside", "/absolute", "", "with/slash"])
def test_invalid_catalog_id(catalog_id: str) -> None:
    content = YAMLReader().read(ASSET)["catalog"]
    content["id"] = catalog_id
    with pytest.raises(ValidationError):
        GemsCatalog.model_validate(content)


def test_catalog_batch_rejects_duplicates_before_writing(dao_10_2: StudyDao, gems_catalog: GemsCatalog) -> None:
    prepare_catalog_taxonomy(dao_10_2)
    with pytest.raises(GemsCatalogAlreadyExists):
        dao_10_2.save_catalogs([gems_catalog, gems_catalog])
    assert dao_10_2.get_catalogs() == []

    dao_10_2.save_catalogs([gems_catalog])
    with pytest.raises(GemsCatalogAlreadyExists):
        dao_10_2.save_catalogs([gems_catalog])
    assert_catalogs_equal(dao_10_2.get_catalogs(), [gems_catalog])

    dao_10_2.save_catalogs([])
    assert_catalogs_equal(dao_10_2.get_catalogs(), [gems_catalog])
    new_catalog = gems_catalog.model_copy(update={"id": "another_catalog"})
    dao_10_2.save_catalogs([new_catalog])
    assert_catalogs_equal(dao_10_2.get_catalogs(), [new_catalog, gems_catalog])


def test_catalog_batch_preserves_metric_fields(dao_10_2: StudyDao) -> None:
    prepare_catalog_taxonomy(dao_10_2)
    content = {
        "id": "catalog",
        "taxonomy": "antares_legacy_taxonomy",
        "location": {"taxonomy-category": "balance"},
        "metrics-definition": [
            {"id": "z", "terms-operator": "sum", "time-operator": "avg"},
            {
                "id": "a",
                "terms-operator": "avg",
                "time-operator": "sum",
                "terms": [],
                "breakdown": None,
                "filter": None,
            },
            {
                "id": "m",
                "terms-operator": "sum",
                "time-operator": "sum",
                "terms": [
                    {"taxonomy-category": "balance", "output-id": "price"},
                    {"taxonomy-category": "balance", "output-id": "cost", "location-port": None},
                ],
                "breakdown": [],
            },
        ],
    }
    catalog = GemsCatalog.model_validate(content)
    empty_catalog = catalog.model_copy(update={"id": "empty_catalog", "metrics_definition": []})
    dao_10_2.save_catalogs([empty_catalog, catalog])
    saved = dao_10_2.get_catalogs()
    assert_catalogs_equal(saved, [catalog, empty_catalog])
    actual_catalog_with_metrics = saved[0].model_dump(mode="json", by_alias=True, exclude_unset=True)
    actual_catalog_with_metrics["metrics-definition"].sort(key=lambda metric: metric["id"])
    expected_metrics = content["metrics-definition"]
    assert isinstance(expected_metrics, list)
    expected_metrics.sort(key=lambda metric: metric["id"])
    assert actual_catalog_with_metrics == content
