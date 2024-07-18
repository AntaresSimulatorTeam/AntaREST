import logging
from typing import List, Optional, Union

from antarest.core.model import JSON
from antarest.study.storage.rawstudy.model.filesystem.lazy_node import LazyNode

logger = logging.getLogger(__name__)


class TsNumbersVector(LazyNode[List[int], List[int], JSON]):
    def load(
        self, url: Optional[List[str]] = None, depth: int = -1, expanded: bool = False, format: Optional[str] = None
    ) -> List[int]:
        file_path, tmp_dir = self._get_real_file_path()

        if file_path.exists():
            with open(file_path, "r") as fh:
                data = fh.readlines()

            if tmp_dir:
                tmp_dir.cleanup()

            if len(data) >= 1:
                return [int(d) for d in data[1:]]

        if tmp_dir:
            tmp_dir.cleanup()
        logger.warning(f"Missing file {self.config.path}")
        return []

    def dump(
        self,
        data: Union[str, bytes, List[int]],
        url: Optional[List[str]] = None,
    ) -> None:
        self.config.path.parent.mkdir(exist_ok=True, parents=True)
        with open(self.config.path, "w") as fh:
            fh.write(f"size:1x{len(data)}\n")
            for d in data:
                fh.write(f"{d}\n")

    def check_errors(
        self,
        data: JSON,
        url: Optional[List[str]] = None,
        raising: bool = False,
    ) -> List[str]:
        return []

    def normalize(self) -> None:
        # this is not normalizable
        pass

    def denormalize(self) -> None:
        # this is not normalizable
        pass
