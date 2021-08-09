from pathlib import Path
from unittest.mock import Mock

from antarest.study.storage.rawstudy.model.filesystem.config.files import (
    ConfigPathBuilder,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import (
    FileStudyTree,
)


def test_renewable_subtree():
    path = Path(__file__).parent / "samples/v810/sample1"
    context: ContextServer = Mock(specs=ContextServer)
    config = ConfigPathBuilder.build(path, "")
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
