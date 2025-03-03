# Copyright (c) 2025, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import contextlib
import functools
import io
import logging
import os
import tempfile
import typing as t
import zipfile
from pathlib import Path

import py7zr
import pydantic_core
from filelock import FileLock
from typing_extensions import override

from antarest.core.exceptions import ShouldNotHappenException
from antarest.core.model import JSON, SUB_JSON
from antarest.core.serde.ini_reader import IniReader, IReader
from antarest.core.serde.ini_writer import IniWriter
from antarest.core.serde.json import from_json
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.inode import INode


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


def log_warning(f: t.Callable[..., t.Any]) -> t.Callable[..., t.Any]:
    """
    Decorator to suppress `UserWarning` exceptions by logging them as warnings.

    Args:
        f: The function or method to be decorated.

    Returns:
        Callable[..., Any]: The decorated function.
    """

    @functools.wraps(f)
    def wrapper(*args: t.Any, **kwargs: t.Any) -> t.Any:
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
        types: t.Optional[t.Dict[str, t.Any]] = None,
        reader: t.Optional[IReader] = None,
        writer: t.Optional[IniWriter] = None,
    ):
        super().__init__(config)
        self.context = context
        self.path = config.path
        self.types = types or {}
        self.reader = reader or IniReader()
        self.writer = writer or IniWriter()

    def _get(
        self,
        url: t.Optional[t.List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        get_node: bool = False,
    ) -> t.Union[SUB_JSON, INode[SUB_JSON, SUB_JSON, JSON]]:
        if get_node:
            return self

        if depth <= -1 and expanded:
            return f"json://{self.config.path.name}"

        if depth == 0:
            return {}

        url = url or []
        kwargs = self._get_filtering_kwargs(url)

        if self.config.archive_path:
            inside_archive_path = self.config.path.relative_to(self.config.archive_path.with_suffix("")).as_posix()
            if self.config.archive_path.suffix == ".zip":
                with zipfile.ZipFile(self.config.archive_path, mode="r") as zipped_folder:
                    with io.TextIOWrapper(zipped_folder.open(inside_archive_path)) as f:
                        data = self.reader.read(f, **kwargs)
            elif self.config.archive_path.suffix == ".7z":
                with py7zr.SevenZipFile(self.config.archive_path, mode="r") as zipped_folder:
                    with io.TextIOWrapper(zipped_folder.read([inside_archive_path])[inside_archive_path]) as f:
                        data = self.reader.read(f, **kwargs)
            else:
                raise ShouldNotHappenException(f"Unsupported archived study format: {self.config.archive_path.suffix}")
        else:
            data = self.reader.read(self.path, **kwargs)

        data = self._handle_urls(data, depth, url)
        return t.cast(SUB_JSON, data)

    @staticmethod
    def _handle_urls(data: t.Dict[str, t.Any], depth: int, url: t.List[str]) -> t.Dict[str, t.Any]:
        if len(url) == 2:
            if url[0] in data and url[1] in data[url[0]]:
                data = data[url[0]][url[1]]
            else:
                # lower keys to find a match
                data = {k.lower(): v for k, v in {k.lower(): v for k, v in data.items()}[url[0].lower()].items()}[
                    url[1].lower()
                ]
        elif len(url) == 1:
            if url[0] in data:
                data = data[url[0]]
            else:
                # lower keys to find a match
                data = {k.lower(): v for k, v in data.items()}[url[0].lower()]

        else:
            data = {k: {} for k in data} if depth == 1 else data
        return data

    # noinspection PyMethodMayBeStatic
    def _get_filtering_kwargs(self, url: t.List[str]) -> t.Dict[str, str]:
        """
        Extracts the filtering arguments from the URL components.

        Note: this method can be overridden in subclasses to provide additional filtering arguments.

        Args:
            url: URL components [section_name, key_name].

        Returns:
            Keyword arguments used by the INI reader to filter the data.
        """
        if len(url) > 2:
            raise ValueError(f"Invalid URL: {url!r}")
        elif len(url) == 2:
            return {"section": url[0], "option": url[1]}
        elif len(url) == 1:
            return {"section": url[0]}
        else:
            return {}

    @override
    def get(
        self,
        url: t.Optional[t.List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        formatted: bool = True,
    ) -> SUB_JSON:
        output = self._get(url, depth, expanded, get_node=False)
        assert not isinstance(output, INode)
        return output

    @override
    def get_node(
        self,
        url: t.Optional[t.List[str]] = None,
    ) -> INode[SUB_JSON, SUB_JSON, JSON]:
        output = self._get(url, get_node=True)
        assert isinstance(output, INode)
        return output

    @override
    def save(self, data: SUB_JSON, url: t.Optional[t.List[str]] = None) -> None:
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
                with contextlib.suppress(pydantic_core.ValidationError):
                    obj = from_json(data)
            if len(url) == 2:
                if url[0] not in info:
                    info[url[0]] = {}
                info[url[0]][url[1]] = obj
            elif len(url) == 1:
                info[url[0]] = obj
            else:
                info = t.cast(JSON, obj)
            self.writer.write(info, self.path)

    @log_warning
    @override
    def delete(self, url: t.Optional[t.List[str]] = None) -> None:
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
                        f"Cannot delete key: Key '{key_name}' not found in section [{section_name}]",
                    ) from None

        self.writer.write(data, self.path)

    @override
    def check_errors(
        self,
        data: JSON,
        url: t.Optional[t.List[str]] = None,
        raising: bool = False,
    ) -> t.List[str]:
        errors = []
        for section, params in self.types.items():
            if section not in data:
                msg = f"section {section} not in {self.__class__.__name__}"
                if raising:
                    raise ValueError(msg)
                errors.append(msg)
            else:
                self._validate_param(section, params, data[section], errors, raising)

        return errors

    @override
    def normalize(self) -> None:
        pass  # no external store in this node

    @override
    def denormalize(self) -> None:
        pass  # no external store in this node

    def _validate_param(
        self,
        section: str,
        params: t.Any,
        data: JSON,
        errors: t.List[str],
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
