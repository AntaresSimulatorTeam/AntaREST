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
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional

import py7zr
import pydantic_core
from filelock import FileLock
from typing_extensions import override

from antarest.core.exceptions import ShouldNotHappenException
from antarest.core.model import JSON, SUB_JSON
from antarest.core.serialization import from_json
from antarest.study.storage.rawstudy.ini_reader import (
    IniReader,
    IReader,
    ReaderOptions,
    SelectionPredicate,
    ini_reader_options,
    make_predicate,
)
from antarest.study.storage.rawstudy.ini_writer import IniWriter
from antarest.study.storage.rawstudy.model.filesystem.config.field_validators import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.inode import INode

SectionMatcher = Callable[[str], str]


def _lower_case(input: str) -> str:
    return input.lower()


LOWER_CASE_MATCHER: SectionMatcher = _lower_case
NAME_TO_ID_MATCHER: SectionMatcher = transform_name_to_id


@dataclass(frozen=True)
class IniLocation:
    """
    Defines a location in INI file data.
    """

    section: Optional[str] = None
    key: Optional[str] = None


def url_to_location(url: List[str]) -> IniLocation:
    if len(url) == 2:
        return IniLocation(section=url[0], key=url[1])
    elif len(url) == 1:
        return IniLocation(section=url[0])
    else:
        return IniLocation()


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
    """
    Common parent class for all INI files.

    Some behaviour can be overriden for specific files, see args.

    Args:
        value_parsers: Defines how specific options should be parsed,
            for example to specify it should be parsed as str, or lower case ...
        section_matcher: Defines how section names are matched when
            retrieving and updating data (for example matching in lower case)
    """

    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        types: t.Optional[t.Dict[str, t.Any]] = None,
        reader: t.Optional[IReader] = None,
        writer: t.Optional[IniWriter] = None,
        section_matcher: Optional[SectionMatcher] = None,
    ):
        super().__init__(config)
        self.context = context
        self.path = config.path
        self.types = types or {}
        self.reader = reader or IniReader()
        self.writer = writer or IniWriter()
        self.section_matcher = section_matcher

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
        options = self._build_options(url)

        if self.config.archive_path:
            inside_archive_path = self.config.path.relative_to(self.config.archive_path.with_suffix("")).as_posix()
            if self.config.archive_path.suffix == ".zip":
                with zipfile.ZipFile(self.config.archive_path, mode="r") as zipped_folder:
                    with io.TextIOWrapper(zipped_folder.open(inside_archive_path)) as f:
                        data = self.reader.read(f, options)
            elif self.config.archive_path.suffix == ".7z":
                with py7zr.SevenZipFile(self.config.archive_path, mode="r") as zipped_folder:
                    with io.TextIOWrapper(zipped_folder.read([inside_archive_path])[inside_archive_path]) as f:
                        data = self.reader.read(f, options)
            else:
                raise ShouldNotHappenException(f"Unsupported archived study format: {self.config.archive_path.suffix}")
        else:
            data = self.reader.read(self.path, options)

        data = self._filter_for_url(data, depth, url)
        return t.cast(SUB_JSON, data)

    def _find_matching_section(self, data: JSON, section: str) -> str:
        if self.section_matcher:
            original_keys = {self.section_matcher(k): k for k in data.keys()}
            matcher = self.section_matcher(section)
            return original_keys.get(matcher, None)
        else:
            return section

    def _filter_for_url(self, data: JSON, depth: int, url: t.List[str]) -> JSON:
        location = url_to_location(url)
        if not location.section and not location.key:
            if depth == 1:  # truncate to only keys
                data = dict((k, {}) for k in data.keys())
            return data
        section = self._find_matching_section(data, location.section)
        section_data = data[section]
        if location.key:
            return section_data[location.key]
        else:
            return section_data

    def _make_section_predicate(self, section: str) -> SelectionPredicate:
        if self.section_matcher:
            return lambda actual_section: self.section_matcher(section) == self.section_matcher(actual_section)
        else:
            return make_predicate(value=section)

    # noinspection PyMethodMayBeStatic
    def _build_options(self, url: t.List[str]) -> ReaderOptions:
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
        loc = url_to_location(url)
        if loc.section and loc.key:
            return ReaderOptions(
                section_predicate=self._make_section_predicate(loc.section), option_predicate=make_predicate(loc.key)
            )
        elif loc.section:
            return ReaderOptions(section_predicate=self._make_section_predicate(loc.section))
        else:
            return ini_reader_options()

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
            existing_data = self.reader.read(self.path) if self.path.exists() else {}
            new_data = data
            if isinstance(data, str):
                with contextlib.suppress(pydantic_core.ValidationError):
                    new_data = from_json(data)

            # Depending on the specified location, the behaviour differs
            loc = url_to_location(url)
            if loc.section and loc.key:
                # Only update the specified option
                section = self._find_matching_section(existing_data, loc.section) or loc.section
                existing_data.setdefault(section, {})[loc.key] = new_data
            elif loc.section:
                # Updates the whole section (replaces the existing data)
                section = self._find_matching_section(existing_data, loc.section) or loc.section
                existing_data[section] = new_data
            else:
                # Replace the whole data
                existing_data = new_data

            self.writer.write(existing_data, self.path)

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

        loc = url_to_location(url)

        data = self.reader.read(self.path)

        if loc.section and loc.key:
            section = self._find_matching_section(data, loc.section)
            if not section:
                raise IniFileNodeWarning(
                    self.config,
                    f"Cannot delete section: Section [{loc.section}] not found",
                )
            try:
                del data[section][loc.key]
            except KeyError:
                raise IniFileNodeWarning(
                    self.config,
                    f"Cannot delete key: Key '{loc.key}' not found in section [{section}]",
                ) from None

        elif loc.section:
            section = self._find_matching_section(data, loc.section)
            if not section:
                raise IniFileNodeWarning(
                    self.config,
                    f"Cannot delete section: Section [{loc.section}] not found",
                )
            del data[section]

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
