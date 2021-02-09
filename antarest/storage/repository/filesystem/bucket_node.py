import glob
import os
from pathlib import Path
from typing import Optional, List

from antarest.common.custom_types import JSON
from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.raw_file_node import RawFileNode


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

    def build(self, config: StudyConfig) -> TREE:
        if not config.path.exists():
            return dict()

        current_dir = os.getcwd()
        os.chdir(self.config.path)

        children: TREE = {
            "/".join(Path(file).parts): RawFileNode(
                self.config.next_file(file)
            )
            for file in glob.glob("**", recursive=True)
            if Path(file).is_file()
        }

        os.chdir(current_dir)
        return children

    def validate(self, data: JSON) -> None:
        pass  # no validation for bucket node
