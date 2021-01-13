import glob
import os
from pathlib import Path
from typing import Optional, List

from api_iso_antares.custom_types import JSON, SUB_JSON
from api_iso_antares.filesystem.config.model import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.raw_file_node import RawFileNode


class BucketNode(FolderNode):
    def get(self, url: Optional[List[str]] = None, depth: int = -1) -> JSON:
        concat_url = "/".join(url or [])
        return FolderNode.get(self, [concat_url])

    def save(self, data: JSON, url: Optional[List[str]] = None) -> None:
        if not self.config.path.exists():
            self.config.path.mkdir()

        if url:
            RawFileNode(config=self.config.next_file(url[0])).save(str(data))
        else:
            for file, content in data.items():
                RawFileNode(config=self.config.next_file(file)).save(
                    str(content)
                )

    def build(self, config: Config) -> TREE:
        current_dir = os.getcwd()
        os.chdir(self.config.path)

        children: TREE = {
            "/".join(Path(file).parts): RawFileNode(
                self.config.next_file(file)
            )
            for file in glob.glob("**", recursive=True)
        }

        os.chdir(current_dir)
        return children

    def validate(self, data: JSON) -> None:
        pass  # no validation for bucket node
