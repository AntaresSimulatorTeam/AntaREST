import shutil
import typing as t
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from zipfile import ZipFile

from antarest.core.exceptions import ChildNotFoundError
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.inode import G, INode, S, V


@dataclass
class SimpleCache:
    value: t.Any
    expiration_date: datetime


class LazyNode(INode, ABC, t.Generic[G, S, V]):  # type: ignore
    """
    Abstract left with implemented a lazy loading for its daughter implementation.
    """

    ZIP_FILELIST_CACHE: t.Dict[str, SimpleCache] = {}

    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
    ) -> None:
        self.context = context
        super().__init__(config)

    def _get_real_file_path(
        self,
    ) -> t.Tuple[Path, t.Any]:
        tmp_dir = None
        if self.config.zip_path:
            path, tmp_dir = self._extract_file_to_tmp_dir()
        else:
            path = self.config.path
        return path, tmp_dir

    def file_exists(self) -> bool:
        if self.config.zip_path:
            str_zipped_path = str(self.config.zip_path)
            inside_zip_path = str(self.config.path)[len(str_zipped_path[:-4]) + 1 :]
            str_inside_zip_path = str(inside_zip_path).replace("\\", "/")
            if str_zipped_path not in LazyNode.ZIP_FILELIST_CACHE:
                with ZipFile(file=self.config.zip_path) as zip_file:
                    LazyNode.ZIP_FILELIST_CACHE[str_zipped_path] = SimpleCache(
                        value=zip_file.namelist(),
                        expiration_date=datetime.utcnow() + timedelta(hours=2),
                    )
            return str_inside_zip_path in LazyNode.ZIP_FILELIST_CACHE[str_zipped_path].value
        else:
            return self.config.path.exists()

    def _get(
        self,
        url: t.Optional[t.List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        format: t.Optional[str] = None,
        get_node: bool = False,
    ) -> t.Union[t.Union[str, G], INode[G, S, V]]:
        self._assert_url_end(url)

        if get_node:
            return self

        if self.get_link_path().exists():
            link = self.get_link_path().read_text()
            if expanded:
                return link
            else:
                return t.cast(G, self.context.resolver.resolve(link, format))

        if expanded:
            return self.get_lazy_content()
        else:
            return self.load(url, depth, expanded, format)

    def get(
        self,
        url: t.Optional[t.List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        format: t.Optional[str] = None,
    ) -> t.Union[str, G]:
        output = self._get(url, depth, expanded, format, get_node=False)
        assert not isinstance(output, INode)
        return output

    def get_node(
        self,
        url: t.Optional[t.List[str]] = None,
    ) -> INode[G, S, V]:
        output = self._get(url, get_node=True)
        assert isinstance(output, INode)
        return output

    def delete(self, url: t.Optional[t.List[str]] = None) -> None:
        self._assert_url_end(url)
        if self.get_link_path().exists():
            self.get_link_path().unlink()
        elif self.config.path.exists():
            self.config.path.unlink()

    def _infer_path(self) -> Path:
        if self.get_link_path().exists():
            return self.get_link_path()
        elif self.config.path.exists():
            return self.config.path
        else:
            raise ChildNotFoundError(
                f"Neither link file {self.get_link_path} nor matrix file {self.config.path} exists"
            )

    def _infer_target_path(self, is_link: bool) -> Path:
        if is_link:
            return self.get_link_path()
        else:
            return self.config.path

    def get_link_path(self) -> Path:
        path = self.config.path.parent / (self.config.path.name + ".link")
        return path

    def save(self, data: t.Union[str, bytes, S], url: t.Optional[t.List[str]] = None) -> None:
        self._assert_not_in_zipped_file()
        self._assert_url_end(url)

        if isinstance(data, str) and self.context.resolver.resolve(data, format="json"):
            self.get_link_path().write_text(data)
            if self.config.path.exists():
                self.config.path.unlink()
            return None

        self.dump(t.cast(S, data), url)
        if self.get_link_path().exists():
            self.get_link_path().unlink()
        return None

    def rename_file(self, target: "LazyNode[t.Any, t.Any, t.Any]") -> None:
        target_path = target._infer_target_path(self.get_link_path().exists())
        target_path.unlink(missing_ok=True)
        self._infer_path().rename(target_path)

    def copy_file(self, target: "LazyNode[t.Any, t.Any, t.Any]") -> None:
        target_path = target._infer_target_path(self.get_link_path().exists())
        target_path.unlink(missing_ok=True)
        shutil.copy(self._infer_path(), target_path)

    def get_lazy_content(
        self,
        url: t.Optional[t.List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
    ) -> str:
        return f"file://{self.config.path.name}"

    @abstractmethod
    def load(
        self,
        url: t.Optional[t.List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        format: t.Optional[str] = None,
    ) -> G:
        """
        Fetch data on disk.

        Args:
            url: data path to retrieve
            depth: after url is reached, node expand tree until matches depth asked
            expanded: context parameter to determine if current node comes from an expansion
            format: ask for raw file transformation

        Returns:

        """
        raise NotImplementedError()

    @abstractmethod
    def dump(self, data: S, url: t.Optional[t.List[str]] = None) -> None:
        """
        Store data on tree.

        Args:
            data: new data to save
            url: data path to change

        Returns:

        """
        raise NotImplementedError()
