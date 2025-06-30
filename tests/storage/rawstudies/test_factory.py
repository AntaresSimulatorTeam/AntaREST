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

from unittest.mock import Mock

from antarest.core.interfaces.cache import study_config_cache_key
from antarest.matrixstore.matrix_uri_mapper import MatrixUriMapper
from antarest.study.storage.rawstudy.model.filesystem.config.files import build
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfigDTO
from antarest.study.storage.rawstudy.model.filesystem.factory import StudyFactory
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree
from tests.storage.rawstudies.samples import ASSETS_DIR


def test_renewable_subtree() -> None:
    path = ASSETS_DIR / "v810/sample1"
    matrix_mapper: MatrixUriMapper = Mock()
    matrix_mapper.get_link_content.return_value = None

    config = build(path, "")
    assert config.get_renewable_ids("area") == ["la_rochelle", "oleron"]

    tree = FileStudyTree(matrix_mapper, config)
    json_tree = tree.get([], depth=-1)
    assert json_tree is not None
    assert json_tree["input"]["renewables"]["series"]["area"] == {
        "la_rochelle": {"series": "matrixfile://series.txt"},
        "oleron": {"series": "matrixfile://series.txt"},
    }
    clusters = tree.get(["input", "renewables", "clusters", "area", "list"], depth=3)
    assert clusters == {
        "la_rochelle": {
            "name": "la_rochelle",
            "group": "solar pv",
            "nominalcapacity": 500.0,
            "unitcount": 3,
            "ts-interpretation": "production-factor",
        },
        "oleron": {
            "name": "oleron",
            "group": "wind offshore",
            "nominalcapacity": 1000.0,
            "unitcount": 2,
            "ts-interpretation": "production-factor",
        },
    }


def test_factory_cache() -> None:
    path = ASSETS_DIR / "v810/sample1"

    cache = Mock()
    matrix_mapper_factory = Mock()
    matrix_mapper = Mock()
    matrix_mapper_factory.create.return_value = matrix_mapper

    factory = StudyFactory(matrix_mapper_factory=matrix_mapper_factory, cache=cache)
    study_id = "study-id"
    cache_id = study_config_cache_key(study_id)
    config = build(path, study_id)

    cache.get.return_value = None
    study = factory.create_from_fs(path, True, study_id)
    assert study.config == config
    cache.put.assert_called_once_with(cache_id, FileStudyTreeConfigDTO.from_build_config(config).model_dump())

    cache.get.return_value = FileStudyTreeConfigDTO.from_build_config(config).model_dump()
    study = factory.create_from_fs(path, True, study_id)
    assert study.config == config
