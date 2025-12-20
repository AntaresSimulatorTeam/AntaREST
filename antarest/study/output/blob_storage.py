from abc import ABC, abstractmethod
from pathlib import Path


class IBlobStorage(ABC):
    """
    Interface for writing and reading "objects" to and from files.

    For now the interface is based on paths. We must take care of not
    having whole blobs in memory, because they could be larger than memory.
    """

    @abstractmethod
    def read_blob(self, blob_id: str, target_path: Path) -> None:
        pass

    @abstractmethod
    def write_blob(self, blob_id: str, src_path: Path) -> None:
        pass

    @abstractmethod
    def delete_blob(self, blob_id: str) -> None:
        pass

    @abstractmethod
    def blob_exists(self, blob_id: str) -> bool:
        pass

    @abstractmethod
    def list_blobs(self) -> str:
        pass
