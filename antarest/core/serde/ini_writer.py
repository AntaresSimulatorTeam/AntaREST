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

import ast
import configparser
from pathlib import Path
from typing import Callable, Dict, List, Optional

from typing_extensions import override

from antarest.core.model import JSON
from antarest.core.serde.ini_common import OptionMatcher, PrimitiveType, any_section_option_matcher

# Value serializers may be used to customize the way INI options are serialized
ValueSerializer = Callable[[str], PrimitiveType]


def _lower_case(input: str) -> str:
    return input.lower()


LOWER_CASE_SERIALIZER: ValueSerializer = _lower_case


class ValueSerializers:
    def __init__(self, serializers: Dict[OptionMatcher, ValueSerializer]):
        self._serializers = serializers

    def find_serializer(self, section: str, key: str) -> Optional[ValueSerializer]:
        if self._serializers:
            possible_keys = [
                OptionMatcher(section=section, key=key),
                any_section_option_matcher(key=key),
            ]
            for k in possible_keys:
                if parser := self._serializers.get(k, None):
                    return parser
        return None


class IniConfigParser(configparser.RawConfigParser):
    def __init__(
        self,
        special_keys: Optional[List[str]] = None,
        value_serializers: Optional[ValueSerializers] = None,
    ) -> None:
        super().__init__()
        self.special_keys = special_keys
        self._value_serializers = value_serializers or ValueSerializers({})

    # noinspection SpellCheckingInspection
    @override
    def optionxform(self, optionstr: str) -> str:
        return optionstr

    def _write_line(  # type:ignore
        self,
        delimiter,
        fp,
        key,
        section_name,
        value,
    ) -> None:
        value = self._interpolation.before_write(  # type:ignore
            self, section_name, key, value
        )
        if self._value_serializers:
            if serializer := self._value_serializers.find_serializer(section_name, key):
                value = serializer(value)
        if value is not None or not self._allow_no_value:  # type:ignore
            value = delimiter + str(value).replace("\n", "\n\t")
        else:
            value = ""
        fp.write(f"{key}{value}\n")

    def _write_section(  # type:ignore
        self,
        fp,
        section_name,
        section_items,
        delimiter,
    ) -> None:
        """Write a single section to the specified `fp`."""
        fp.write(f"[{section_name}]\n")
        for key, value in section_items:
            if self.special_keys and key in self.special_keys and isinstance(ast.literal_eval(value), list):
                for sub_value in ast.literal_eval(value):
                    self._write_line(delimiter, fp, key, section_name, sub_value)
            else:
                self._write_line(delimiter, fp, key, section_name, value)
        fp.write("\n")


class IniWriter:
    """
    Standard INI writer.
    """

    def __init__(
        self,
        special_keys: Optional[List[str]] = None,
        value_serializers: Optional[Dict[OptionMatcher, ValueSerializer]] = None,
    ):
        self.special_keys = special_keys
        self._value_serializers = ValueSerializers(value_serializers or {})

    def write(self, data: JSON, path: Path) -> None:
        """
        Write `.ini` file from JSON content

        Args:
            data: JSON content.
            path: path to `.ini` file.
        """
        config_parser = IniConfigParser(special_keys=self.special_keys, value_serializers=self._value_serializers)
        config_parser.read_dict(data)
        with path.open("w") as fp:
            config_parser.write(fp)


class SimpleKeyValueWriter(IniWriter):
    """
    Simple key/value INI writer.
    """

    @override
    def write(self, data: JSON, path: Path) -> None:
        """
        Write `.ini` file from JSON content

        Args:
            data: JSON content.
            path: path to `.ini` file.
        """
        with path.open("w") as fp:
            for key, value in data.items():
                if value is not None:
                    fp.write(f"{key}={value}\n")
