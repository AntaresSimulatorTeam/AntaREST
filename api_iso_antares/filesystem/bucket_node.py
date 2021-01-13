import glob
import os
from typing import Optional, List

from api_iso_antares.custom_types import JSON
from api_iso_antares.filesystem.config.model import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.raw_file_node import RawFileNode


class BucketNode(FolderNode):
    def get(self, url: Optional[List[str]] = None, depth: int = -1) -> JSON:
        concat_url = "/".join(url or [])
        return FolderNode.get(self, [concat_url])

    def build(self, config: Config) -> TREE:
        current_dir = os.getcwd()
        os.chdir(self.config.path)

        children: TREE = {
            file: RawFileNode(self.config.next_file(file))
            for file in glob.glob("**", recursive=True)
        }

        os.chdir(current_dir)
        return children

    def validate(self, data: JSON) -> None:
        pass  # no validation for bucket node
