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
import dataclasses
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional, Pattern, Sequence, TextIO, TypeAlias, cast

from typing_extensions import override

from antarest.core.model import JSON
from antarest.core.serde.ini_common import OptionMatcher, PrimitiveType, any_section_option_matcher

ValueParser: TypeAlias = Callable[[str], PrimitiveType]


def _lower_case(input: str) -> str:
    return input.lower()


def _to_string(input: Any) -> str:
    return str(input)


LOWER_CASE_PARSER: ValueParser = _lower_case
STRING_PARSER: ValueParser = _to_string


def _convert_value(value: str) -> PrimitiveType:
    """Convert value to the appropriate type for JSON."""

    try:
        # Infinity values are not supported by JSON, so we use a string instead.
        mapping = {"true": True, "false": False, "+inf": "+Inf", "-inf": "-Inf", "inf": "+Inf"}
        return cast(PrimitiveType, mapping[value.lower()])
    except KeyError:
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value


class ValueParsers:
    def __init__(self, default_parser: ValueParser, parsers: Dict[OptionMatcher, ValueParser]):
        self._default_parser = default_parser
        self._parsers = parsers

    def find_parser(self, section: str, key: str) -> ValueParser:
        if self._parsers:
            possible_keys = [
                OptionMatcher(section=section, key=key),
                any_section_option_matcher(key=key),
            ]
            for k in possible_keys:
                if parser := self._parsers.get(k, None):
                    return parser

        return self._default_parser


@dataclasses.dataclass(frozen=True)
class IniFilter:
    """
    Filter sections and options in an INI file based on regular expressions.

    Attributes:
        section_regex: A compiled regex for matching section names.
        option_regex: A compiled regex for matching option names.
    """

    section_regex: Optional[Pattern[str]] = None
    option_regex: Optional[Pattern[str]] = None

    @classmethod
    def from_kwargs(
        cls,
        section: str = "",
        option: str = "",
        section_regex: Optional[str | Pattern[str]] = None,
        option_regex: Optional[str | Pattern[str]] = None,
        **_unused: Any,  # ignore unknown options
    ) -> "IniFilter":
        """
        Create an instance from given filtering parameters.

        When using `section` or `option` parameters, an exact match is done.
        Alternatively, one can use `section_regex` or `option_regex` to perform a full match using a regex.

        Args:
            section: The section name to match (by default, all sections are matched)
            option: The option name to match (by default, all options are matched)
            section_regex: The regex for matching section names.
            option_regex: The regex for matching option names.
            _unused: Placeholder for any unknown options.

        Returns:
            The newly created instance
        """
        if section:
            section_regex = re.compile(re.escape(section), re.IGNORECASE)
        if option:
            option_regex = re.compile(re.escape(option), re.IGNORECASE)
        if isinstance(section_regex, str):
            section_regex = re.compile(section_regex, re.IGNORECASE) if section_regex else None
        if isinstance(option_regex, str):
            option_regex = re.compile(option_regex, re.IGNORECASE) if option_regex else None
        return cls(section_regex=section_regex, option_regex=option_regex)

    def select_section_option(self, section: str, option: str = "") -> bool:
        """
        Check if a given section and option match the regular expressions.

        Args:
            section: The section name to match.
            option: The option name to match (optional).

        Returns:
            Whether the section and option match their respective regular expressions.
        """
        if self.section_regex and not self.section_regex.fullmatch(section):
            return False
        if self.option_regex and option and not self.option_regex.fullmatch(option):
            return False
        return True


class IReader(ABC):
    """
    File reader interface.
    """

    @abstractmethod
    def read(self, path: Any, **kwargs: Any) -> JSON:
        """
        Parse `.ini` file to json object.

        Args:
            path:    Path to `.ini` file or file-like object.
            options: Additional options used for reading.

        Returns:
            Dictionary of parsed `.ini` file which can be converted to JSON.
        """


class IniReader(IReader):
    """
    Custom `.ini` reader for `.ini` files which have duplicate keys in a section.

    This class is required, to parse `settings/generaldata.ini` files which
    has duplicate keys like "playlist_year_weight", "playlist_year +", "playlist_year -",
    "select_var -", "select_var +", in the `[playlist]` section.

    For instance::

        [playlist]
        playlist_reset = false
        playlist_year + = 6
        playlist_year + = 8
        playlist_year + = 13

    It is also required to parse `input/areas/sets.ini` files which have keys like "+" or "-".

    For instance::

        [all areas]
        caption = All areas
        comments = Spatial aggregates on all areas
        + = east
        + = west

    This class is not compatible with standard `.ini` readers.
    """

    def __init__(
        self,
        special_keys: Sequence[str] = (),
        section_name: str = "settings",
        value_parsers: Dict[OptionMatcher, ValueParser] | None = None,
    ) -> None:
        super().__init__()

        # Default section name to use if `.ini` file has no section.
        self._special_keys = set(special_keys)
        self._value_parsers = ValueParsers(default_parser=_convert_value, parsers=value_parsers or {})

        # List of keys which should be parsed as list.
        self._section_name = section_name

        # Dictionary of parsed sections and options
        self._curr_sections: Dict[str, Dict[str, Any]] = {}

        # Current section name used during paring
        self._curr_section = ""

        # Current option name used during paring
        self._curr_option = ""

    @override
    def __repr__(self) -> str:  # pragma: no cover
        """Return a string representation of the object."""
        cls = self.__class__.__name__
        # use getattr() to make sure that the attributes are defined
        special_keys = tuple(getattr(self, "_special_keys", ()))
        section_name = getattr(self, "_section_name", "settings")
        return f"{cls}(special_keys={special_keys!r}, section_name={section_name!r})"

    @override
    def read(self, path: Any, **kwargs: Any) -> JSON:
        if isinstance(path, (Path, str)):
            try:
                with open(path, mode="r", encoding="utf-8") as f:
                    sections = self._parse_ini_file(f, **kwargs)
            except UnicodeDecodeError:
                # On windows, `.ini` files may use "cp1252" encoding
                with open(path, mode="r", encoding="cp1252") as f:
                    sections = self._parse_ini_file(f, **kwargs)
            except FileNotFoundError:
                # If the file is missing, an empty dictionary is returned.
                # This is required to mimic the behavior of `configparser.ConfigParser`.
                return {}

        elif hasattr(path, "read"):
            with path:
                sections = self._parse_ini_file(path, **kwargs)

        else:  # pragma: no cover
            raise TypeError(repr(type(path)))

        return cast(JSON, sections)

    def _parse_ini_file(self, ini_file: TextIO, **kwargs: Any) -> JSON:
        """
        Parse `.ini` file to JSON object.

        The following parsing rules are applied:

        - If the file has no section, then the default section name is used.
          This case is required to parse Xpansion `user/expansion/settings.ini` files
          (using `SimpleKeyValueReader` subclass).

        - If the file has duplicate sections, then the values are merged.
          This case is required when the end-user produced an ill-formed `.ini` file.
          This ensures the parsing is robust even if some values may be lost.

        - If a section has duplicate keys, then the values are merged.
          This case is required, for instance, to parse `settings/generaldata.ini` files which
          has duplicate keys like "playlist_year_weight", "playlist_year +", "playlist_year -",
          "select_var -", "select_var +", in the `[playlist]` section.
          In this case, duplicate keys must be declared in the `special_keys` argument,
          to parse them as list.

        - If a section has no key, then an empty dictionary is returned.
          This case is required to parse `input/hydro/prepro/correlation.ini` files.

        - If a section name has square brackets, then they are preserved.
          This case is required to parse `input/hydro/allocation/{area-id}.ini` files.

        Args:
            ini_file: file or file-like object.

        Keywords:
            - section: The section name to match (by default, all sections are matched)
            - option: The option name to match (by default, all options are matched)
            - section_regex: The regex for matching section names.
            - option_regex: The regex for matching option names.

        Returns:
            Dictionary of parsed `.ini` file which can be converted to JSON.
        """
        ini_filter = IniFilter.from_kwargs(**kwargs)

        # NOTE: This algorithm is 1.93x faster than configparser.ConfigParser
        section_name = self._section_name

        # reset the current values
        self._curr_sections.clear()
        self._curr_section = ""
        self._curr_option = ""

        for line in ini_file:
            line = line.strip()
            if not line or line.startswith(";") or line.startswith("#"):
                continue
            elif line.startswith("["):
                section_name = line[1:-1]
                stop = self._handle_section(ini_filter, section_name)
            elif "=" in line:
                key, value = map(str.strip, line.split("=", 1))
                stop = self._handle_option(ini_filter, section_name, key, value)
            else:
                raise ValueError(f"☠☠☠ Invalid line: {line!r}")

            # Stop parsing if the filter don't match
            if stop:
                break

        return self._curr_sections

    def _handle_section(self, ini_filter: IniFilter, section: str) -> bool:
        # state: a new section is found
        match = ini_filter.select_section_option(section)

        if self._curr_section:
            # state: option parsing is finished
            if match:
                self._append_section(section)
                return False
            # prematurely stop parsing if the filter don't match
            return True

        if match:
            self._append_section(section)

        # continue parsing to the next section
        return False

    def _append_section(self, section: str) -> None:
        self._curr_sections.setdefault(section, {})
        self._curr_section = section
        self._curr_option = ""

    def _handle_option(self, ini_filter: IniFilter, section: str, key: str, value: str) -> bool:
        # state: a new option is found (which may be a duplicate)
        match = ini_filter.select_section_option(section, key)

        if self._curr_option:
            if match:
                self._append_option(section, key, value)
                return False
            # prematurely stop parsing if the filter don't match
            return not ini_filter.select_section_option(section)

        if match:
            self._append_option(section, key, value)
        # continue parsing to the next option
        return False

    def _append_option(self, section: str, key: str, value: str) -> None:
        self._curr_sections.setdefault(section, {})
        values = self._curr_sections[section]
        parser = self._value_parsers.find_parser(section, key)
        parsed = parser(value)
        if key in self._special_keys:
            values.setdefault(key, []).append(parsed)
        else:
            values[key] = parsed
        self._curr_option = key


class SimpleKeyValueReader(IniReader):
    """
    Simple INI reader for "settings.ini" file which has no section.
    """

    @override
    def read(self, path: Any, **kwargs: Any) -> JSON:
        """
        Parse `.ini` file which has no section to JSON object.

        This class is required to parse Xpansion `user/expansion/settings.ini` files.

        Args:
            path: Path to `.ini` file or file-like object.
            kwargs: Additional options used for reading.

        Returns:
            Dictionary of parsed key/value pairs.
        """
        sections = super().read(path)
        obj = cast(Mapping[str, JSON], sections)
        return obj[self._section_name]


def read_ini(source: Path | TextIO) -> JSON:
    """
    Parses the provided content as a 2-levels dictionary.
    """
    return IniReader().read(source)
