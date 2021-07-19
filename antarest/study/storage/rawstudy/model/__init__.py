from dataclasses import dataclass

from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import (
    FileStudyTree,
)


@dataclass
class FileStudy:
    config: FileStudyTreeConfig
    tree: FileStudyTree
