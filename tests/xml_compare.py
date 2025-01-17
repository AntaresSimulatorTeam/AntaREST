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

import re
import typing as t
from xml.etree.ElementTree import Element


def compare_elements(elem1: Element, elem2: Element, parents: t.Tuple[str, ...] = ()) -> str:
    # Compare tags
    xpath = "".join(f"/{p}" for p in parents)
    if elem1.tag != elem2.tag:
        return f"Tag mismatch: {xpath} '{elem1.tag}' != '{elem2.tag}'"

    # Compare attributes
    if elem1.attrib != elem2.attrib:
        return f"Attrib mismatch: {xpath} {elem1.attrib!r} != {elem2.attrib!r}"

    # Compare text content (normalize whitespace)
    text1 = re.sub(r"\s+", " ", elem1.text.strip()) if elem1.text else ""
    text2 = re.sub(r"\s+", " ", elem2.text.strip()) if elem2.text else ""
    if text1 != text2:
        return f"Text mismatch: {xpath} {elem1.text!r} != {elem2.text!r}"

    # Compare children
    if len(elem1) != len(elem2):
        return f"Children mismatch: {xpath} {len(elem1)} != {len(elem2)}"

    parent: str = re.sub(r"^\{[^}]+}", "", elem1.tag)
    for child1, child2 in zip(elem1, elem2):
        if err_msg := compare_elements(child1, child2, parents=parents + (parent,)):
            return err_msg

    # no error
    return ""
