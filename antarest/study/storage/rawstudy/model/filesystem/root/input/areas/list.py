from typing import Optional, List

from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import (
    INode,
)


class InputAreasList(INode[List[str], List[str], List[str]]):
    def normalize(self) -> None:
        pass  # no external store in this node

    def denormalize(self) -> None:
        pass  # no external store in this node

    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        super().__init__(config)
        self.context = context

    def get_node(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        formatted: bool = True,
    ) -> INode[List[str], List[str], List[str]]:
        return self

    def get(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        formatted: bool = True,
    ) -> List[str]:
        if self.config.zip_path:
            path, tmp_dir = self._extract_file_to_tmp_dir()
            lines = path.read_text().split("\n")
            tmp_dir.cleanup()
        else:
            lines = self.config.path.read_text().split("\n")
        return [l.strip() for l in lines if l.strip()]

    def save(self, data: List[str], url: Optional[List[str]] = None) -> None:
        self._assert_not_in_zipped_file()
        self.config.path.write_text("\n".join(data))

    def delete(self, url: Optional[List[str]] = None) -> None:
        if self.config.path.exists():
            self.config.path.unlink()

    def check_errors(
        self,
        data: List[str],
        url: Optional[List[str]] = None,
        raising: bool = False,
    ) -> List[str]:

        errors = []
        if any(
            a not in data
            for a in [area.name for area in self.config.areas.values()]
        ):
            errors.append(
                f"list.txt should have {self.config.area_names()} nodes but given {data}"
            )
        return errors
