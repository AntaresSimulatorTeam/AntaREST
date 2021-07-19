from dataclasses import dataclass

from antarest.storage.repository.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.repository.filesystem.root.filestudytree import (
    FileStudyTree,
)


@dataclass
class FileStudy:
    config: FileStudyTreeConfig
    tree: FileStudyTree
