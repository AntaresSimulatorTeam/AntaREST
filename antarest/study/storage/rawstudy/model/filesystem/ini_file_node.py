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
import io
import logging
import os
import tempfile
import zipfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

import py7zr
import pydantic_core
from filelock import FileLock
from typing_extensions import override

from antarest.core.exceptions import ShouldNotHappenException
from antarest.core.model import JSON, SUB_JSON
from antarest.core.serde.ini_reader import (
    IniReader,
    IReader,
)
from antarest.core.serde.ini_writer import IniWriter
from antarest.core.serde.json import from_json
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.inode import INode

logger = logging.getLogger(__name__)


class IniFileNodeWarning(UserWarning):
    """
    Custom User Warning subclass for INI file-related warnings.

    This warning class is designed to provide more informative warning messages for INI file errors.

    Args:
        message: The specific warning message.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


@dataclass(frozen=True)
class IniMatch(ABC):
    """
    Represents a match of a sub-part of INI file content.
    """

    def __bool__(self) -> bool:
        """
        True if a match has been found.
        """
        return True

    @abstractmethod
    def get_part(self) -> SUB_JSON:
        """
        The content of the matched sub-part.
        """
        pass

    def replace_part(self, new_part: SUB_JSON) -> JSON:
        """
        Replaces the content of the matched sub-part,
        and returns the whole updated content.
        """
        raise NotImplementedError()

    def delete_part(self) -> JSON:
        """
        Removes the content of the matched sub-part,
        and returns the whole updated content.
        """
        raise NotImplementedError()


@dataclass(frozen=True)
class SectionMatch(IniMatch):
    data: JSON
    req_section: str
    matched_section: str | None = None

    @override
    def __bool__(self) -> bool:
        return bool(self.matched_section)

    @override
    def get_part(self) -> JSON:
        if not self.matched_section:
            raise KeyError(f"Could not match section {self.req_section}")
        return cast(JSON, self.data[self.matched_section])

    @override
    def replace_part(self, new_part: SUB_JSON) -> JSON:
        section = self.matched_section or self.req_section
        self.data[section] = new_part
        return self.data

    @override
    def delete_part(self) -> JSON:
        if not self.matched_section:
            raise IniFileNodeWarning(f"Cannot delete section: Section [{self.req_section}] not found")
        del self.data[self.matched_section]
        return self.data


@dataclass(frozen=True)
class OptionMatch(IniMatch):
    data: JSON
    req_section: str
    req_option: str
    matched_section: str | None = None
    matched_option: str | None = None

    @override
    def __bool__(self) -> bool:
        return bool(self.matched_section) and bool(self.matched_option)

    @override
    def get_part(self) -> SUB_JSON:
        if not self.matched_section:
            raise KeyError(f"Could not match section {self.req_section}")
        if not self.matched_option:
            raise KeyError(f"Could not match option {self.req_option}")
        return cast(SUB_JSON, self.data[self.matched_section][self.matched_option])

    @override
    def replace_part(self, new_part: SUB_JSON) -> JSON:
        section_data = self.data.setdefault(self.matched_section or self.req_section, {})
        section_data[self.matched_option or self.req_option] = new_part
        return self.data

    @override
    def delete_part(self) -> JSON:
        if not self.matched_section:
            raise IniFileNodeWarning(f"Cannot delete key: Section [{self.req_section}] not found")
        if not self.matched_option:
            raise IniFileNodeWarning(
                f"Cannot delete key: Key '{self.req_option}' not found in section [{self.matched_section}]"
            )
        del self.data[self.matched_section][self.matched_option]
        return self.data


@dataclass(frozen=True)
class OnlySections(IniMatch):
    data: JSON

    @override
    def get_part(self) -> SUB_JSON:
        return {k: {} for k in self.data}


@dataclass(frozen=True)
class WholeFile(IniMatch):
    data: JSON

    @override
    def get_part(self) -> JSON:
        return self.data

    @override
    def replace_part(self, new_part: Any) -> JSON:
        return cast(JSON, new_part)


def _match_exact_or_lower(data: JSON, key: str) -> str | None:
    """
    Tries to match one of the keys as-is, or in lowercase.
    """
    if key in data:
        return key
    lower = key.lower()
    for k in data:
        if k.lower() == lower:
            return k
    return None


def _match_section(data: JSON, section: str) -> SectionMatch:
    matched_section = _match_exact_or_lower(data, section)
    return SectionMatch(data=data, req_section=section, matched_section=matched_section)


def _match_option(data: JSON, section: str, option: str) -> OptionMatch:
    section_match = _match_section(data, section)
    if not section_match:
        return OptionMatch(data=data, req_section=section, req_option=option)
    section_data = section_match.get_part()
    matched_option = _match_exact_or_lower(section_data, option)
    return OptionMatch(
        data=data,
        req_section=section,
        req_option=option,
        matched_section=section_match.matched_section,
        matched_option=matched_option,
    )


def _match_url(data: JSON, url: List[str], depth: int | None = None) -> IniMatch:
    if len(url) == 2:
        return _match_option(data, section=url[0], option=url[1])
    elif len(url) == 1:
        return _match_section(data, section=url[0])
    else:
        if depth == 1:
            return OnlySections(data)
        return WholeFile(data)


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
    ) -> SUB_JSON | INode[SUB_JSON, SUB_JSON, JSON]:
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

        return _match_url(data, url, depth).get_part()

        # noinspection PyMethodMayBeStatic

    def _get_filtering_kwargs(self, url: List[str]) -> Dict[str, str]:
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
        url: Optional[List[str]] = None,
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
        url: Optional[List[str]] = None,
    ) -> INode[SUB_JSON, SUB_JSON, JSON]:
        output = self._get(url, get_node=True)
        assert isinstance(output, INode)
        return output

    @override
    def save(self, data: SUB_JSON, url: Optional[List[str]] = None) -> None:
        self._assert_not_in_zipped_file()
        url = url or []
        with FileLock(
            str(
                Path(tempfile.gettempdir())
                / f"{self.config.study_id}-{self.path.relative_to(self.config.study_path).name.replace(os.sep, '.')}.lock"
            )
        ):
            existing_data = self.reader.read(self.path) if self.path.exists() else {}
            new_data = data
            if isinstance(new_data, str):
                with contextlib.suppress(pydantic_core.ValidationError):
                    new_data = from_json(new_data)

            updated_data = _match_url(existing_data, url).replace_part(new_data)

            self.writer.write(updated_data, self.path)

    @override
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
        try:
            if not self.path.exists():
                raise IniFileNodeWarning(f"Cannot delete item {url!r}: Config file not found")

            if not url:
                self.config.path.unlink()
                return

            url_len = len(url)
            if url_len > 2:
                raise IniFileNodeWarning(f"Cannot delete item {url!r}: URL should be fully resolved")

            data = self.reader.read(self.path)
            data = _match_url(data, url).delete_part()
            self.writer.write(data, self.path)

        except IniFileNodeWarning as w:
            relpath = self.config.path.relative_to(self.config.study_path).as_posix()
            logger.warning(f"INI File error '{relpath}': {w}")

    @override
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
