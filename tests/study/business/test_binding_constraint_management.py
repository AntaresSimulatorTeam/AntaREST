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

import typing as t

import pytest

from antarest.study.business.binding_constraint_management import (
    ClusterTerm,
    ConstraintFilters,
    ConstraintOutput,
    ConstraintOutput830,
    ConstraintOutput870,
    ConstraintOutputBase,
    ConstraintTerm,
    LinkTerm,
)


class TestConstraintFilter:
    def test_init(self) -> None:
        bc_filter = ConstraintFilters()
        assert not bc_filter.bc_id
        assert not bc_filter.enabled
        assert not bc_filter.operator
        assert not bc_filter.comments
        assert not bc_filter.group
        assert not bc_filter.time_step
        assert not bc_filter.area_name
        assert not bc_filter.cluster_name
        assert not bc_filter.link_id
        assert not bc_filter.cluster_id

    @pytest.mark.parametrize("bc_id, expected", [("bc1", True), ("BC1", False), ("bc2", False), ("", True)])
    @pytest.mark.parametrize("cls", [ConstraintOutputBase, ConstraintOutput870])
    def test_filter_by__bc_id(self, bc_id: str, expected: bool, cls: t.Type[ConstraintOutput]) -> None:
        """
        The filter should match if the `bc_id` is equal to the constraint's `bc_id` or if the filter is empty.
        Comparisons should be case-sensitive.
        """
        bc_filter = ConstraintFilters(bc_id=bc_id)
        constraint = cls(id="bc1", name="BC1")
        assert bc_filter.match_filters(constraint) == expected, ""

    @pytest.mark.parametrize("enabled, expected", [(True, True), (False, False), (None, True)])
    @pytest.mark.parametrize("cls", [ConstraintOutputBase, ConstraintOutput870])
    def test_filter_by__enabled(self, enabled: t.Optional[bool], expected: bool, cls: t.Type[ConstraintOutput]) -> None:
        """
        The filter should match if the `enabled` is equal to the constraint's `enabled` or if the filter is empty.
        """
        bc_filter = ConstraintFilters(enabled=enabled)
        constraint = cls(id="bc1", name="BC1")
        assert bc_filter.match_filters(constraint) == expected

    @pytest.mark.parametrize("operator, expected", [("equal", True), ("both", False), (None, True)])
    @pytest.mark.parametrize("cls", [ConstraintOutputBase, ConstraintOutput870])
    def test_filter_by__operator(self, operator: str, expected: bool, cls: t.Type[ConstraintOutput]) -> None:
        """
        The filter should match if the `operator` is equal to the constraint's `operator` or if the filter is empty.
        """
        bc_filter = ConstraintFilters(operator=operator)
        constraint = cls(id="bc1", name="BC1", operator="equal")
        assert bc_filter.match_filters(constraint) == expected

    @pytest.mark.parametrize("comments, expected", [("hello", True), ("HELLO", True), ("goodbye", False), ("", True)])
    @pytest.mark.parametrize("cls", [ConstraintOutputBase, ConstraintOutput870])
    def test_filter_by__comments(self, comments: str, expected: bool, cls: t.Type[ConstraintOutput]) -> None:
        """
        The filter should match if the constraint's `comments` contains the filter's `comments` or if the filter is empty.
        Comparisons should be case-insensitive.
        """
        bc_filter = ConstraintFilters(comments=comments)
        constraint = cls(id="bc1", name="BC1", comments="Say hello!")
        assert bc_filter.match_filters(constraint) == expected

    @pytest.mark.parametrize("group, expected", [("grp1", False), ("grp2", False), ("", True)])
    def test_filter_by__group(self, group: str, expected: bool) -> None:
        """
        The filter should never match if the filter's `group` is not empty.
        """
        bc_filter = ConstraintFilters(group=group)
        for cls in [ConstraintOutputBase, ConstraintOutput830, ConstraintOutput870]:
            constraint = cls(id="bc1", name="BC1")
            assert bc_filter.match_filters(constraint) == expected

    @pytest.mark.parametrize("group, expected", [("grp1", True), ("GRP1", True), ("grp2", False), ("", True)])
    def test_filter_by__group_with_existing_group(self, group: str, expected: bool) -> None:
        """
        The filter should match if the `group` is equal to the constraint's `group` or if the filter is empty.
        Comparisons should be case-insensitive.
        """
        bc_filter = ConstraintFilters(group=group)
        constraint = ConstraintOutput870(id="bc1", name="BC1", group="Grp1")
        assert bc_filter.match_filters(constraint) == expected

    @pytest.mark.parametrize("time_step, expected", [("hourly", True), ("daily", False), (None, True)])
    @pytest.mark.parametrize("cls", [ConstraintOutputBase, ConstraintOutput870])
    def test_filter_by__time_step(self, time_step: str, expected: bool, cls: t.Type[ConstraintOutput]) -> None:
        """
        The filter should match if the `time_step` is hourly to the constraint's `time_step` or if the filter is empty.
        """
        bc_filter = ConstraintFilters(time_step=time_step)
        constraint = cls(id="bc1", name="BC1", time_step="hourly")
        assert bc_filter.match_filters(constraint) == expected

    @pytest.mark.parametrize(
        "area_name, expected",
        [("FR", True), ("fr", True), ("DE", True), ("IT", True), ("HU", True), ("EN", False), ("", True)],
    )
    @pytest.mark.parametrize("cls", [ConstraintOutputBase, ConstraintOutput870])
    def test_filter_by__area_name(self, area_name: str, expected: bool, cls: t.Type[ConstraintOutput]) -> None:
        """
        The filter should match if one of the constraint's terms has an area name which contains
        the filter's area name or if the filter is empty.
        Comparisons should be case-insensitive.
        """
        bc_filter = ConstraintFilters(area_name=area_name)
        constraint = cls(id="bc1", name="BC1")
        constraint.terms.extend(
            [
                ConstraintTerm(weight=2.0, offset=5, data=LinkTerm(area1="area_FR_x", area2="area_DE_x")),
                ConstraintTerm(weight=3.0, offset=5, data=LinkTerm(area1="area_IT_y", area2="area_DE_y")),
                ConstraintTerm(weight=2.0, offset=5, data=ClusterTerm(area="area_HU_z", cluster="area_CL1_z")),
            ]
        )
        assert bc_filter.match_filters(constraint) == expected

    @pytest.mark.parametrize(
        "cluster_name, expected",
        [("cl1", True), ("CL1", True), ("cl2", False), ("", True)],
    )
    @pytest.mark.parametrize("cls", [ConstraintOutputBase, ConstraintOutput870])
    def test_filter_by__cluster_name(self, cluster_name: str, expected: bool, cls: t.Type[ConstraintOutput]) -> None:
        """
        The filter should match if one of the constraint's terms has a cluster name which contains
        the filter's cluster name or if the filter is empty.
        Comparisons should be case-insensitive.
        """
        bc_filter = ConstraintFilters(cluster_name=cluster_name)
        constraint = cls(id="bc1", name="BC1")
        constraint.terms.extend(
            [
                ConstraintTerm(weight=2.0, offset=5, data=LinkTerm(area1="area_FR_x", area2="area_DE_x")),
                ConstraintTerm(weight=3.0, offset=5, data=LinkTerm(area1="area_IT_y", area2="area_DE_y")),
                ConstraintTerm(weight=2.0, offset=5, data=ClusterTerm(area="area_HU_z", cluster="area_CL1_z")),
            ]
        )
        assert bc_filter.match_filters(constraint) == expected

    @pytest.mark.parametrize(
        "link_id, expected",
        [
            ("area_DE_x%area_FR_x", True),
            ("AREA_DE_X%area_FR_x", True),
            ("area_DE_x%AREA_FR_X", True),
            ("AREA_DE_X%AREA_FR_X", True),
            ("area_FR_x%area_DE_x", False),
            ("fr%de", False),
            ("", True),
        ],
    )
    @pytest.mark.parametrize("cls", [ConstraintOutputBase, ConstraintOutput870])
    def test_filter_by__link_id(self, link_id: str, expected: bool, cls: t.Type[ConstraintOutput]) -> None:
        """
        The filter should match if one of the constraint's terms has a cluster name which contains
        the filter's cluster name or if the filter is empty.
        Comparisons should be case-insensitive.
        """
        bc_filter = ConstraintFilters(link_id=link_id)
        constraint = cls(id="bc1", name="BC1")
        constraint.terms.extend(
            [
                ConstraintTerm(weight=2.0, offset=5, data=LinkTerm(area1="area_FR_x", area2="area_DE_x")),
                ConstraintTerm(weight=3.0, offset=5, data=LinkTerm(area1="area_IT_y", area2="area_DE_y")),
                ConstraintTerm(weight=2.0, offset=5, data=ClusterTerm(area="area_HU_z", cluster="area_CL1_z")),
            ]
        )
        assert bc_filter.match_filters(constraint) == expected

    @pytest.mark.parametrize(
        "cluster_id, expected",
        [
            ("area_HU_z.area_CL1_z", True),
            ("AREA_HU_Z.area_CL1_z", True),
            ("area_HU_z.AREA_CL1_Z", True),
            ("AREA_HU_Z.AREA_CL1_Z", True),
            ("HU.CL1", False),
            ("", True),
        ],
    )
    @pytest.mark.parametrize("cls", [ConstraintOutputBase, ConstraintOutput870])
    def test_filter_by__cluster_id(self, cluster_id: str, expected: bool, cls: t.Type[ConstraintOutput]) -> None:
        """
        The filter should match if one of the constraint's terms has a cluster name which contains
        the filter's cluster name or if the filter is empty.
        Comparisons should be case-insensitive.
        """
        bc_filter = ConstraintFilters(cluster_id=cluster_id)
        constraint = cls(id="bc1", name="BC1")
        constraint.terms.extend(
            [
                ConstraintTerm(weight=2.0, offset=5, data=LinkTerm(area1="area_FR_x", area2="area_DE_x")),
                ConstraintTerm(weight=3.0, offset=5, data=LinkTerm(area1="area_IT_y", area2="area_DE_y")),
                ConstraintTerm(weight=2.0, offset=5, data=ClusterTerm(area="area_HU_z", cluster="area_CL1_z")),
            ]
        )
        assert bc_filter.match_filters(constraint) == expected
