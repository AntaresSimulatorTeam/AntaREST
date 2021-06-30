import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List, cast

from antarest.common.custom_types import JSON, SUB_JSON
from antarest.matrixstore.model import MatrixDTO, MatrixFreq
from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.context import ContextServer
from antarest.storage.repository.filesystem.lazy_node import LazyNode


class MatrixNode(LazyNode[JSON, JSON, JSON], ABC):
    def __init__(
        self, context: ContextServer, config: StudyConfig, freq: str
    ) -> None:
        LazyNode.__init__(self, context, config)
        self.freq = freq

    def get_lazy_content(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
    ) -> str:
        return f"matrix://{self.config.path.name}"

    @abstractmethod
    def load(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
    ) -> JSON:
        """
        Fetch data on disk.

        Args:
            url: data path to retrieve
            depth: after url is reached, node expand tree until matches depth asked
            expanded: context parameter to determine if current node become from a expansion

        Returns:

        """
        raise NotImplementedError()

    @abstractmethod
    def dump(self, data: JSON, url: Optional[List[str]] = None) -> None:
        """
        Store data on tree.

        Args:
            data: new data to save
            url: data path to change

        Returns:

        """
        raise NotImplementedError()
