from dataclasses import dataclass

from antarest.storage.business.rawstudy.model.filesystem import (
    FileStudyTreeConfig,
)
from antarest.storage.business.rawstudy.model.filesystem.root.filestudytree import (
    FileStudyTree,
)


@dataclass
class FileStudy:
    config: FileStudyTreeConfig
    tree: FileStudyTree
