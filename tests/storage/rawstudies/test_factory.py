from pathlib import Path
from unittest.mock import Mock

from antarest.core.interfaces.cache import CacheConstants
from antarest.study.storage.rawstudy.model.filesystem.config.files import build
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfigDTO,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import (
    StudyFactory,
)
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import (
    FileStudyTree,
)


def test_renewable_subtree():
    path = Path(__file__).parent / "samples/v810/sample1"
    context: ContextServer = Mock(specs=ContextServer)
    config = build(path, "")
    assert config.get_renewable_names("area") == ["la_rochelle", "oleron"]

    tree = FileStudyTree(context, config)
    json_tree = tree.get([], depth=-1)
    assert json_tree is not None
    assert json_tree["input"]["renewables"]["series"]["area"] == {
        "la_rochelle": {"series": "matrixfile://series.txt"},
        "oleron": {"series": "matrixfile://series.txt"},
    }
    clusters = tree.get(
        ["input", "renewables", "clusters", "area", "list"], depth=3
    )
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


def test_factory_cache():
    path = Path(__file__).parent / "samples/v810/sample1"

    cache = Mock()
    factory = StudyFactory(matrix=Mock(), resolver=Mock(), cache=cache)
    study_id = "study-id"
    cache_id = f"{CacheConstants.STUDY_FACTORY}/{study_id}"
    config = build(path, study_id)

    cache.get.return_value = None
    study = factory.create_from_fs(path, study_id)
    assert study.config == config
    cache.put.assert_called_once_with(
        cache_id, FileStudyTreeConfigDTO.from_build_config(config).dict()
    )

    cache.get.return_value = FileStudyTreeConfigDTO.from_build_config(
        config
    ).dict()
    study = factory.create_from_fs(path, study_id)
    assert study.config == config
