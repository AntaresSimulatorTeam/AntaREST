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

ASSET = Path(__file__).parent / "assets/gems/catalogs/antares_legacy_area_catalog.yml"


def test_catalogs_roundtrip(dao_10_2: StudyDao, gems_catalog: GemsCatalog) -> None:
    assert dao_10_2.get_catalogs() == []
    # The fixture comes from AntaresLegacyModels-to-GEMS-Converter.
    expected = YAMLReader().read(ASSET)["catalog"]
    dao_10_2.save_catalog(gems_catalog)
    saved = dao_10_2.get_catalogs()
    assert len(saved) == 1
    assert saved[0].model_dump(mode="json", by_alias=True, exclude_unset=True) == expected
    assert ReadOnlyAdapter(dao_10_2).get_catalogs() == saved

    other = gems_catalog.model_copy(update={"id": "another_catalog"})
    dao_10_2.save_catalog(other)
    assert dao_10_2.get_catalogs() == [other, gems_catalog]

    with pytest.raises(GemsCatalogAlreadyExists):
        dao_10_2.save_catalog(gems_catalog.model_copy(update={"taxonomy": "another_taxonomy"}))
    assert dao_10_2.get_catalogs() == [other, gems_catalog]


def test_location_ports_is_rejected() -> None:
    content = YAMLReader().read(ASSET)["catalog"]
    term = content["metrics-definition"][0]["terms"][0]
    term["location-ports"] = term.pop("location-port")
    with pytest.raises(ValidationError, match="location-ports"):
        GemsCatalog.model_validate(content)


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
