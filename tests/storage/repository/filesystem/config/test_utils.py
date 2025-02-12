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

import string

import pytest

from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id

VALID_CHARS = "azAZ09_-(),&"


@pytest.mark.parametrize(
    "name, expected",
    [("France", "france"), ("@é'rFf", "rff"), ("t@é'rFf", "t rff")],
)
def test_transform_name_to_id__nominal_case(name, expected):
    assert transform_name_to_id(name) == expected


@pytest.mark.parametrize("name", VALID_CHARS)
def test_transform_name_to_id__valid_chars(name):
    assert transform_name_to_id(name, lower=True) == name.lower()
    assert transform_name_to_id(name, lower=False) == name


@pytest.mark.parametrize("name", sorted(set(string.punctuation) - set(VALID_CHARS)))
def test_transform_name_to_id__punctuation(name):
    assert not transform_name_to_id(name)


@pytest.mark.parametrize("name", sorted(set(string.whitespace) - set(VALID_CHARS)))
def test_transform_name_to_id__whitespace(name):
    assert not transform_name_to_id(name)


@pytest.mark.parametrize(
    "name, expected",
    [
        ("$$foo", "foo"),
        ("bar$$", "bar"),
        # inner invalid chars are replaced by one space
        ("foo$$$bar", "foo bar"),
        ("$$foo$$$bar$$", "foo bar"),
    ],
)
def test_transform_name_to_id__strip_invalid_duplicates(name, expected):
    assert transform_name_to_id(name) == expected


@pytest.mark.parametrize(
    "name, expected",
    [
        ("  foo", "foo"),
        ("bar  ", "bar"),
        # inner whitespaces are preserved
        ("foo   bar", "foo   bar"),
        ("  foo   bar  ", "foo   bar"),
    ],
)
def test_transform_name_to_id__strip_whitespaces(name, expected):
    assert transform_name_to_id(name) == expected
