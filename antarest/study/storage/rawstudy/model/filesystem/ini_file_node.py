import contextlib
import functools
import io
import json
import logging
import os
import tempfile
import zipfile
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union, cast

from antarest.core.model import JSON, SUB_JSON
from antarest.study.storage.rawstudy.io.reader import IniReader
from antarest.study.storage.rawstudy.io.reader.ini_reader import IReader
from antarest.study.storage.rawstudy.io.writer.ini_writer import IniWriter
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import INode
from filelock import FileLock


class IniFileNodeWarning(UserWarning):
    """
    Custom User Warning subclass for INI file-related warnings.

    This warning class is designed to provide more informative warning messages for INI file errors.

    Args:
        config: The configuration associated with the INI file.
        message: The specific warning message.
    """

    def __init__(self, config: FileStudyTreeConfig, message: str) -> None:
        relpath = config.path.relative_to(config.study_path).as_posix()
        super().__init__(f"INI File error '{relpath}': {message}")


def log_warning(f: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to suppress `UserWarning` exceptions by logging them as warnings.

    Args:
        f: The function or method to be decorated.

    Returns:
        Callable[..., Any]: The decorated function.
    """

    @functools.wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return f(*args, **kwargs)
        except UserWarning as w:
            # noinspection PyUnresolvedReferences
            logging.getLogger(f.__module__).warning(str(w))

    return wrapper


class IniFileNode(INode[SUB_JSON, SUB_JSON, JSON]):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        types: Optional[Dict[str, Any]] = None,
        reader: Optional[IReader] = None,
        writer: Optional[IniWriter] = None,
    ):
        super().__init__(config)
        self.context = context
        self.path = config.path
        self.types = types or {}
        self.reader = reader or IniReader()
        self.writer = writer or IniWriter()

    def _get(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        get_node: bool = False,
    ) -> Union[SUB_JSON, INode[SUB_JSON, SUB_JSON, JSON]]:
        if get_node:
            return self

        if depth <= -1 and expanded:
            return f"json://{self.config.path.name}"

        if depth == 0:
            return {}
        url = url or []

        if self.config.zip_path:
            with zipfile.ZipFile(
                self.config.zip_path, mode="r"
            ) as zipped_folder:
                inside_zip_path = self.config.path.relative_to(
                    self.config.zip_path.with_suffix("")
                ).as_posix()
                with io.TextIOWrapper(
                    zipped_folder.open(inside_zip_path)
                ) as f:
                    data = self.reader.read(f)
        else:
            data = self.reader.read(self.path)

        if len(url) == 2:
            data = data[url[0]][url[1]]
        elif len(url) == 1:
            data = data[url[0]]
        else:
            data = {k: {} for k in data} if depth == 1 else data
        return cast(SUB_JSON, data)

    def get(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        formatted: bool = True,
    ) -> SUB_JSON:
        output = self._get(url, depth, expanded, get_node=False)
        assert not isinstance(output, INode)
        return output

    def get_node(
        self,
        url: Optional[List[str]] = None,
    ) -> INode[SUB_JSON, SUB_JSON, JSON]:
        output = self._get(url, get_node=True)
        assert isinstance(output, INode)
        return output

    def save(self, data: SUB_JSON, url: Optional[List[str]] = None) -> None:
        self._assert_not_in_zipped_file()
        url = url or []
        with FileLock(
            str(
                Path(tempfile.gettempdir())
                / f"{self.config.study_id}-{self.path.relative_to(self.config.study_path).name.replace(os.sep, '.')}.lock"
            )
        ):
            info = self.reader.read(self.path) if self.path.exists() else {}
            obj = data
            if isinstance(data, str):
                with contextlib.suppress(JSONDecodeError):
                    obj = json.loads(data)
            if len(url) == 2:
                if url[0] not in info:
                    info[url[0]] = {}
                info[url[0]][url[1]] = obj
            elif len(url) == 1:
                info[url[0]] = obj
            else:
                info = cast(JSON, obj)
            self.writer.write(info, self.path)

    @log_warning
    def delete(self, url: Optional[List[str]] = None) -> None:
        """
        Deletes the specified section or key from the INI file,
        or the entire INI file if no URL is provided.

        Args:
            url: A list containing the URL components [section_name, key_name].

        Raises:
            IniFileNodeWarning:
                If the specified section or key cannot be deleted due to errors such as
                missing configuration file, non-resolved URL, or non-existent section/key.
        """
        if not self.path.exists():
            raise IniFileNodeWarning(
                self.config,
                "fCannot delete item {url!r}: Config file not found",
            )

        if not url:
            self.config.path.unlink()
            return

        url_len = len(url)
        if url_len > 2:
            raise IniFileNodeWarning(
                self.config,
                f"Cannot delete item {url!r}: URL should be fully resolved",
            )

        data = self.reader.read(self.path)

        if url_len == 1:
            section_name = url[0]
            try:
                del data[section_name]
            except KeyError:
                raise IniFileNodeWarning(
                    self.config,
                    f"Cannot delete section: Section [{section_name}] not found",
                ) from None

        elif url_len == 2:
            section_name, key_name = url
            try:
                section = data[section_name]
            except KeyError:
                raise IniFileNodeWarning(
                    self.config,
                    f"Cannot delete key: Section [{section_name}] not found",
                ) from None
            else:
                try:
                    del section[key_name]
                except KeyError:
                    raise IniFileNodeWarning(
                        self.config,
                        f"Cannot delete key: Key '{key_name}'"
                        f" not found in section [{section_name}]",
                    ) from None

        self.writer.write(data, self.path)

    def check_errors(
        self,
        data: JSON,
        url: Optional[List[str]] = None,
        raising: bool = False,
    ) -> List[str]:
        errors = []
        for section, params in self.types.items():
            if section not in data:
                msg = f"section {section} not in {self.__class__.__name__}"
                if raising:
                    raise ValueError(msg)
                errors.append(msg)
            else:
                self._validate_param(
                    section, params, data[section], errors, raising
                )

        return errors

    def normalize(self) -> None:
        pass  # no external store in this node

    def denormalize(self) -> None:
        pass  # no external store in this node

    def _validate_param(
        self,
        section: str,
        params: Any,
        data: JSON,
        errors: List[str],
        raising: bool,
    ) -> None:
        for param, typing in params.items():
            if param not in data:
                msg = f"param {param} of section {section} not in {self.__class__.__name__}"
                if raising:
                    raise ValueError(msg)
                errors.append(msg)
            elif not isinstance(data[param], typing):
                msg = f"param {param} of section {section} in {self.__class__.__name__} bad type"
                if raising:
                    raise ValueError(msg)
                errors.append(msg)
