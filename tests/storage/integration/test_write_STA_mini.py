# Copyright (c) 2026, RTE (https://www.rte-france.com)
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

from typing import Optional

import numpy as np
import polars as pl
import pytest
from polars.testing import assert_frame_equal

from antarest.core.model import SUB_JSON
from antarest.core.utils.polars import create_polars_dataframe
from antarest.study.service import StudyService
from tests.helpers import with_admin_user
from tests.storage.integration.conftest import UUID


def assert_with_errors(
    storage_service: StudyService,
    url: str,
    new: SUB_JSON,
    expected: SUB_JSON = None,
) -> None:
    url = url[len("/v1/studies/") :]
    uuid, url = url.split("/raw?path=")
    res = storage_service.edit_study(uuid=uuid, url=url, new=new)
    assert res == new

    res = storage_service.get_raw_content(uuid=uuid, path=url, depth=-1, formatted=True)
    if expected is not None:
        if isinstance(expected, pl.DataFrame):
            assert_frame_equal(expected, res, check_dtypes=False)
        else:
            assert res == expected
    else:
        assert res == new


@with_admin_user
@pytest.mark.parametrize(
    "url, new",
    [
        (
            f"/v1/studies/{UUID}/raw?path=settings/generaldata/general/horizon",
            3000,
        ),
    ],
)
def test_sta_mini_settings(storage_service: StudyService, url: str, new: SUB_JSON) -> None:
    assert_with_errors(storage_service=storage_service, url=url, new=new)


@with_admin_user
@pytest.mark.parametrize(
    "url, new",
    [
        (
            f"/v1/studies/{UUID}/raw?path=layers/layers/activeLayer/showAllLayer",
            False,
        ),
    ],
)
def test_sta_mini_layers_layers(storage_service: StudyService, url: str, new: SUB_JSON) -> None:
    assert_with_errors(storage_service=storage_service, url=url, new=new)


@with_admin_user
@pytest.mark.parametrize(
    "url, new",
    [
        (
            f"/v1/studies/{UUID}/raw?path=Desktop/.shellclassinfo",
            {
                "iconfile": "This is a test",
                "iconindex": 42,
                "infotip": "Hello",
            },
        ),
        (
            f"/v1/studies/{UUID}/raw?path=Desktop/.shellclassinfo/iconindex",
            42,
        ),
    ],
)
def test_sta_mini_desktop(storage_service: StudyService, url: str, new: SUB_JSON) -> None:
    assert_with_errors(storage_service=storage_service, url=url, new=new)


@with_admin_user
@pytest.mark.parametrize(
    "url, new",
    [
        (
            f"/v1/studies/{UUID}/raw?path=study/antares/created",
            42,
        ),
        (
            f"/v1/studies/{UUID}/raw?path=study/antares/author",
            "John Smith",
        ),
    ],
)
def test_sta_mini_study_antares(storage_service: StudyService, url: str, new: SUB_JSON) -> None:
    assert_with_errors(storage_service=storage_service, url=url, new=new)


@with_admin_user
@pytest.mark.parametrize(
    "url, new, expected",
    [
        (
            f"/v1/studies/{UUID}/raw?path=input/bindingconstraints/bindingconstraints",
            {},
            None,
        ),
        (
            f"/v1/studies/{UUID}/raw?path=input/areas/sets/all areas/output",
            True,
            None,
        ),
        (
            f"/v1/studies/{UUID}/raw?path=input/areas/de/optimization/nodal optimization/spread-spilled-energy-cost",
            42,
            None,
        ),
        (f"/v1/studies/{UUID}/raw?path=input/areas/de/ui/layerX/0", 42, None),
        (
            f"/v1/studies/{UUID}/raw?path=input/hydro/allocation/de/[allocation]/de",
            42,
            None,
        ),
        (f"/v1/studies/{UUID}/raw?path=input/load/prepro/fr/k", [[0]], create_polars_dataframe(data=np.array([[0.0]]))),
        (
            f"/v1/studies/{UUID}/raw?path=input/load/series/load_fr",
            [[i] for i in range(100)],
            create_polars_dataframe(data=np.array([[i] for i in range(100)])),
        ),
        (
            f"/v1/studies/{UUID}/raw?path=input/hydro/prepro/correlation/general/mode",
            "hourly",
            None,
        ),
        (
            f"/v1/studies/{UUID}/raw?path=input/hydro/prepro/fr/prepro/prepro/intermonthly-correlation",
            0.42,
            None,
        ),
        (
            f"/v1/studies/{UUID}/raw?path=input/hydro/hydro/inter-monthly-breakdown/fr",
            43,
            None,
        ),
        (
            f"/v1/studies/{UUID}/raw?path=input/thermal/clusters/fr/list/05_nuclear/marginal-cost",
            42,
            None,
        ),
        (
            f"/v1/studies/{UUID}/raw?path=input/links/fr/properties/it/hurdles-cost",
            False,
            None,
        ),
    ],
)
def test_sta_mini_input(storage_service: StudyService, url: str, new: SUB_JSON, expected: Optional[SUB_JSON]) -> None:
    assert_with_errors(storage_service=storage_service, url=url, new=new, expected=expected)


@with_admin_user
@pytest.mark.parametrize(
    "url, new",
    [
        (
            f"/v1/studies/{UUID}/raw?path=output/20201014-1430adq/about-the-study/parameters/general/horizon",
            2042,
        ),
        (
            f"/v1/studies/{UUID}/raw?path=output/20201014-1422eco-hello/about-the-study/study/antares/author",
            "John Smith",
        ),
        (
            f"/v1/studies/{UUID}/raw?path=output/20201014-1422eco-hello/info/general/version",
            42,
        ),
    ],
)
def test_sta_mini_output(storage_service: StudyService, url: str, new: SUB_JSON) -> None:
    assert_with_errors(storage_service=storage_service, url=url, new=new)
