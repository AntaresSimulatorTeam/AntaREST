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

import io
import textwrap
from pathlib import Path

from antarest.core.serde.ini_common import OptionMatcher, any_section_option_matcher
from antarest.core.serde.ini_reader import LOWER_CASE_PARSER, IniReader, SimpleKeyValueReader, ValueParsers


def test_lower_case_parser() -> None:
    assert LOWER_CASE_PARSER("Hello") == "hello"


class TestValueParsers:
    def test_find_value_parsers(self):
        def default(input: str) -> str:
            return "default"

        def custom_exact_match(input: str) -> str:
            return "custom-exact"

        def custom_any_section_match(input: str) -> str:
            return "custom-any-section"

        parsers = ValueParsers(
            default_parser=default,
            parsers={
                OptionMatcher("section1", "option1"): custom_exact_match,
                any_section_option_matcher("option2"): custom_any_section_match,
            },
        )

        assert parsers.find_parser("section1", "option1")("test") == "custom-exact"
        assert parsers.find_parser("section1", "option2")("test") == "custom-any-section"
        assert parsers.find_parser("section1", "option3")("test") == "default"


class TestIniReader:
    def test_read__nominal_case(self, tmp_path: Path) -> None:
        path = Path(tmp_path) / "test.ini"
        path.write_text(
            textwrap.dedent(
                """
                [part1]
                key_int = 1
                key_float = 2.1
                key_big_float = 1e16
                key_small_float = -1e-16
                key_inf = +Inf
                key_str = value1
                key_empty =

                [part2]
                key_bool = True
                key_bool2 = false
                # key_foo = False
                ; key_bar = 3.14
                """
            )
        )

        reader = IniReader()
        actual = reader.read(path)

        expected = {
            "part1": {
                "key_int": 1,
                "key_str": "value1",
                "key_float": 2.1,
                "key_big_float": 1e16,
                "key_small_float": -1e-16,
                "key_inf": "+Inf",  # note: `+Inf` is not supported by JSON
                "key_empty": "",
            },
            "part2": {
                "key_bool": True,
                "key_bool2": False,
            },
        }
        assert actual == expected

        with path.open() as f:
            actual_from_bytes = reader.read(f)
            assert actual_from_bytes == expected

    def test_read__without_section(self) -> None:
        """
        If the file has no section, then the default section name is used.
        This case is required to parse Xpansion `user/expansion/settings.ini` files
        (using `SimpleKeyValueReader` subclass).
        """
        reader = IniReader(section_name="config")
        actual = reader.read(
            io.StringIO(
                """
                key_int = 1
                key_float = 2.1
                key_str = value1
                key_inf = +Inf
                """
            )
        )
        expected = {
            "config": {
                "key_int": 1,
                "key_str": "value1",
                "key_float": 2.1,
                "key_inf": "+Inf",  # note: `+Inf` is not supported by JSON
            },
        }
        assert actual == expected

    def test_read__duplicate_sections(self) -> None:
        """
        If the file has duplicate sections, then the values are merged.
        This case is required when the end-user produced an ill-formed `.ini` file.
        """
        reader = IniReader()
        actual = reader.read(
            io.StringIO(
                """
                [part1]
                key_int = 1
                key_float = 2.1
                key_str = value1

                [part1]
                key_str = value2
                key_bool = True
                """
            )
        )
        expected = {
            "part1": {
                "key_int": 1,
                "key_str": "value2",
                "key_float": 2.1,
                "key_bool": True,
            },
        }
        assert actual == expected

    def test_read__duplicate_keys(self) -> None:
        """
        If a section has duplicate keys, then the values are merged.
        This case is required, for instance, to parse `settings/generaldata.ini` files which
        has duplicate keys like "playlist_year_weight", "playlist_year +", "playlist_year -",
        "select_var -", "select_var +", in the `[playlist]` section.
        In this case, duplicate keys must be declared in the `special_keys` argument,
        to parse them as list.
        """
        reader = IniReader(
            special_keys=[
                "playlist_year_weight",
                "playlist_year +",
                "playlist_year -",
                "select_var -",
                "select_var +",
            ]
        )
        actual = reader.read(
            io.StringIO(
                """
                [part1]
                key_int = 1
                key_int = 2
                
                [playlist]
                playlist_reset = false
                playlist_year_weight = 1
                playlist_year + = 2015
                playlist_year + = 2016
                playlist_year + = 2017
                playlist_year - = 2018
                playlist_year - = 2019
                playlist_year - = 2020
                select_var - = 1
                select_var + = 2
                """
            )
        )
        expected = {
            "part1": {"key_int": 2},  # last value is kept
            "playlist": {
                "playlist_reset": False,
                "playlist_year_weight": [1],
                "playlist_year +": [2015, 2016, 2017],
                "playlist_year -": [2018, 2019, 2020],
                "select_var -": [1],
                "select_var +": [2],
            },
        }
        assert actual == expected

    def test_read__no_key(self) -> None:
        """
        If a section has no key, then an empty dictionary is returned.
        This case is required to parse `input/hydro/prepro/correlation.ini` files.
        """
        reader = IniReader()
        actual = reader.read(
            io.StringIO(
                """
                [part1]
                key_int = 1
                
                [part2]
                """
            )
        )
        expected = {
            "part1": {"key_int": 1},
            "part2": {},
        }
        assert actual == expected

    def test_read__with_square_brackets(self) -> None:
        """
        If a section name has square brackets, then they are preserved.
        This case is required to parse `input/hydro/allocation/{area-id}.ini` files.
        """
        reader = IniReader()
        actual = reader.read(
            io.StringIO(
                """
                [part1]
                key_int = 1
                
                [[allocation]]
                my_area = 2.718
                """
            )
        )
        expected = {
            "part1": {"key_int": 1},
            "[allocation]": {"my_area": 2.718},
        }
        assert actual == expected

    def test_read__sets(self) -> None:
        """
        It is also required to parse `input/areas/sets.ini` files which have keys like "+" or "-".
        """
        reader = IniReader(["+", "-"])
        actual = reader.read(
            io.StringIO(
                """
                [all areas]
                caption = All areas
                comments = Spatial aggregates on all areas
                + = east
                + = west
                """
            )
        )
        expected = {
            "all areas": {
                "caption": "All areas",
                "comments": "Spatial aggregates on all areas",
                "+": ["east", "west"],
            },
        }
        assert actual == expected

    def test_read__filtered_section(self, tmp_path) -> None:
        path = Path(tmp_path) / "test.ini"
        path.write_text(
            textwrap.dedent(
                """
                [part1]
                foo = 5
                bar = hello

                [part2]
                foo = 6
                bar = salut

                [other]
                pi = 3.14
                """
            )
        )

        reader = IniReader()

        # exact match
        actual = reader.read(path, section="part1")
        expected = {"part1": {"foo": 5, "bar": "hello"}}
        assert actual == expected

        # regex match
        actual = reader.read(path, section_regex="part.*")
        expected = {
            "part1": {"foo": 5, "bar": "hello"},
            "part2": {"foo": 6, "bar": "salut"},
        }
        assert actual == expected

    def test_read__filtered_option(self, tmp_path) -> None:
        path = Path(tmp_path) / "test.ini"
        path.write_text(
            textwrap.dedent(
                """
                [part1]
                foo = 5
                bar = hello

                [part2]
                foo = 6
                bar = salut

                [other]
                pi = 3.14
                """
            )
        )

        reader = IniReader()

        # exact match
        actual = reader.read(path, option="foo")
        expected = {"part1": {"foo": 5}, "part2": {"foo": 6}, "other": {}}
        assert actual == expected

        # regex match
        actual = reader.read(path, option_regex="fo.*")
        expected = {"part1": {"foo": 5}, "part2": {"foo": 6}, "other": {}}
        assert actual == expected

        # exact match with section
        actual = reader.read(path, section="part2", option="foo")
        expected = {"part2": {"foo": 6}}
        assert actual == expected

        # regex match with section
        actual = reader.read(path, section_regex="part.*", option="foo")
        expected = {"part1": {"foo": 5}, "part2": {"foo": 6}}
        assert actual == expected

        # regex match with section and option
        actual = reader.read(path, section_regex="part.*", option_regex=".*a.*")
        expected = {"part1": {"bar": "hello"}, "part2": {"bar": "salut"}}
        assert actual == expected

    def test_read__with_custom_parser(self, tmp_path):
        path = Path(tmp_path) / "test.ini"
        path.write_text(
            textwrap.dedent(
                """
                [part1]
                bar = Hello
                
                [part2]
                bar = Hello
                """
            )
        )

        def double_parser(value: str) -> str:
            return value + value

        value_parsers = {OptionMatcher("part2", "bar"): double_parser}
        actual = IniReader(value_parsers=value_parsers).read(path)
        expected = {"part1": {"bar": "Hello"}, "part2": {"bar": "HelloHello"}}
        assert actual == expected

        value_parsers = {any_section_option_matcher("bar"): double_parser}
        actual = IniReader(value_parsers=value_parsers).read(path)
        expected = {"part1": {"bar": "HelloHello"}, "part2": {"bar": "HelloHello"}}
        assert actual == expected


class TestSimpleKeyValueReader:
    def test_read(self) -> None:
        # sample extracted from `user/expansion/settings.ini`
        settings = textwrap.dedent(
            """
            master=relaxed
            uc_type=expansion_fast
            optimality_gap=10001.0
            relative_gap=1e-06
            relaxed_optimality_gap=1e-05
            max_iteration=20
            solver=Xpress
            log_level=3
            separation_parameter=0.66
            batch_size=102
            yearly-weights=
            additional-constraints=constraintsFile.txt
            timelimit=1000000000000
            """
        )
        ini_reader = SimpleKeyValueReader(section_name="dummy")
        actual = ini_reader.read(io.StringIO(settings))

        expected = {
            "master": "relaxed",
            "uc_type": "expansion_fast",
            "optimality_gap": 10001.0,
            "relative_gap": 1e-06,
            "relaxed_optimality_gap": 1e-05,
            "max_iteration": 20,
            "solver": "Xpress",
            "log_level": 3,
            "separation_parameter": 0.66,
            "batch_size": 102,
            "yearly-weights": "",
            "additional-constraints": "constraintsFile.txt",
            "timelimit": 1000000000000,
        }
        assert actual == expected
