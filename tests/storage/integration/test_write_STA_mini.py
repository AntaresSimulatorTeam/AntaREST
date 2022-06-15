from typing import Optional

import pytest

from antarest.core.model import SUB_JSON
from antarest.core.jwt import JWTUser, JWTGroup
from antarest.core.requests import (
    RequestParameters,
)
from antarest.core.roles import RoleType
from antarest.study.service import StudyService
from tests.storage.integration.data.de_details_hourly import de_details_hourly

ADMIN = JWTUser(
    id=1,
    impersonator=1,
    type="users",
    groups=[JWTGroup(id="admin", name="admin", role=RoleType.ADMIN)],
)


def assert_with_errors(
    storage_service: StudyService,
    url: str,
    new: SUB_JSON,
    expected: SUB_JSON = None,
) -> None:
    url = url[len("/v1/studies/") :]
    uuid, url = url.split("/raw?path=")
    params = RequestParameters(user=ADMIN)
    res = storage_service.edit_study(
        uuid=uuid, url=url, new=new, params=params
    )
    assert res == new

    res = storage_service.get(
        uuid=uuid, url=url, depth=-1, formatted=True, params=params
    )
    if expected is not None:
        assert res == expected
    else:
        assert res == new


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, new",
    [
        (
            "/v1/studies/STA-mini/raw?path=settings/generaldata/general/horizon",
            3000,
        ),
    ],
)
def test_sta_mini_settings(storage_service, url: str, new: SUB_JSON):
    assert_with_errors(
        storage_service=storage_service,
        url=url,
        new=new,
    )


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, new",
    [
        (
            "/v1/studies/STA-mini/raw?path=layers/layers/activeLayer/showAllLayer",
            False,
        ),
    ],
)
def test_sta_mini_layers_layers(storage_service, url: str, new: SUB_JSON):
    assert_with_errors(
        storage_service=storage_service,
        url=url,
        new=new,
    )


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, new",
    [
        (
            "/v1/studies/STA-mini/raw?path=layers/layers/activeLayer/showAllLayer",
            False,
        ),
    ],
)
def test_sta_mini_layers_layers(storage_service, url: str, new: SUB_JSON):
    assert_with_errors(
        storage_service=storage_service,
        url=url,
        new=new,
    )


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, new",
    [
        (
            "/v1/studies/STA-mini/raw?path=Desktop/.shellclassinfo",
            {
                "iconfile": "This is a test",
                "iconindex": 42,
                "infotip": "Hello",
            },
        ),
        (
            "/v1/studies/STA-mini/raw?path=Desktop/.shellclassinfo/iconindex",
            42,
        ),
    ],
)
def test_sta_mini_desktop(storage_service, url: str, new: SUB_JSON):
    assert_with_errors(
        storage_service=storage_service,
        url=url,
        new=new,
    )


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, new",
    [
        (
            "/v1/studies/STA-mini/raw?path=study/antares/created",
            42,
        ),
        (
            "/v1/studies/STA-mini/raw?path=study/antares/author",
            "John Smith",
        ),
    ],
)
def test_sta_mini_study_antares(storage_service, url: str, new: SUB_JSON):
    assert_with_errors(
        storage_service=storage_service,
        url=url,
        new=new,
    )


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, new, expected",
    [
        (
            "/v1/studies/STA-mini/raw?path=input/bindingconstraints/bindingconstraints",
            {},
            None,
        ),
        (
            "/v1/studies/STA-mini/raw?path=input/areas/sets/all areas/output",
            True,
            None,
        ),
        (
            "/v1/studies/STA-mini/raw?path=input/areas/de/optimization/nodal optimization/spread-spilled-energy-cost",
            42,
            None,
        ),
        ("/v1/studies/STA-mini/raw?path=input/areas/de/ui/layerX/0", 42, None),
        (
            "/v1/studies/STA-mini/raw?path=input/hydro/allocation/de/[allocation]/de",
            42,
            None,
        ),
        (
            "/v1/studies/STA-mini/raw?path=input/load/prepro/fr/k",
            [[0]],
            {"data": [[0.0]], "index": [0], "columns": [0]},
        ),
        (
            "/v1/studies/STA-mini/raw?path=input/load/series/load_fr",
            [[i] for i in range(100)],
            {
                "data": [
                    [0.0],
                    [1.0],
                    [2.0],
                    [3.0],
                    [4.0],
                    [5.0],
                    [6.0],
                    [7.0],
                    [8.0],
                    [9.0],
                    [10.0],
                    [11.0],
                    [12.0],
                    [13.0],
                    [14.0],
                    [15.0],
                    [16.0],
                    [17.0],
                    [18.0],
                    [19.0],
                    [20.0],
                    [21.0],
                    [22.0],
                    [23.0],
                    [24.0],
                    [25.0],
                    [26.0],
                    [27.0],
                    [28.0],
                    [29.0],
                    [30.0],
                    [31.0],
                    [32.0],
                    [33.0],
                    [34.0],
                    [35.0],
                    [36.0],
                    [37.0],
                    [38.0],
                    [39.0],
                    [40.0],
                    [41.0],
                    [42.0],
                    [43.0],
                    [44.0],
                    [45.0],
                    [46.0],
                    [47.0],
                    [48.0],
                    [49.0],
                    [50.0],
                    [51.0],
                    [52.0],
                    [53.0],
                    [54.0],
                    [55.0],
                    [56.0],
                    [57.0],
                    [58.0],
                    [59.0],
                    [60.0],
                    [61.0],
                    [62.0],
                    [63.0],
                    [64.0],
                    [65.0],
                    [66.0],
                    [67.0],
                    [68.0],
                    [69.0],
                    [70.0],
                    [71.0],
                    [72.0],
                    [73.0],
                    [74.0],
                    [75.0],
                    [76.0],
                    [77.0],
                    [78.0],
                    [79.0],
                    [80.0],
                    [81.0],
                    [82.0],
                    [83.0],
                    [84.0],
                    [85.0],
                    [86.0],
                    [87.0],
                    [88.0],
                    [89.0],
                    [90.0],
                    [91.0],
                    [92.0],
                    [93.0],
                    [94.0],
                    [95.0],
                    [96.0],
                    [97.0],
                    [98.0],
                    [99.0],
                ],
                "index": [
                    0,
                    1,
                    2,
                    3,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                    10,
                    11,
                    12,
                    13,
                    14,
                    15,
                    16,
                    17,
                    18,
                    19,
                    20,
                    21,
                    22,
                    23,
                    24,
                    25,
                    26,
                    27,
                    28,
                    29,
                    30,
                    31,
                    32,
                    33,
                    34,
                    35,
                    36,
                    37,
                    38,
                    39,
                    40,
                    41,
                    42,
                    43,
                    44,
                    45,
                    46,
                    47,
                    48,
                    49,
                    50,
                    51,
                    52,
                    53,
                    54,
                    55,
                    56,
                    57,
                    58,
                    59,
                    60,
                    61,
                    62,
                    63,
                    64,
                    65,
                    66,
                    67,
                    68,
                    69,
                    70,
                    71,
                    72,
                    73,
                    74,
                    75,
                    76,
                    77,
                    78,
                    79,
                    80,
                    81,
                    82,
                    83,
                    84,
                    85,
                    86,
                    87,
                    88,
                    89,
                    90,
                    91,
                    92,
                    93,
                    94,
                    95,
                    96,
                    97,
                    98,
                    99,
                ],
                "columns": [0],
            },
        ),
        (
            "/v1/studies/STA-mini/raw?path=input/hydro/prepro/correlation/general/mode",
            "hourly",
            None,
        ),
        (
            "/v1/studies/STA-mini/raw?path=input/hydro/prepro/fr/prepro/prepro/intermonthly-correlation",
            0.42,
            None,
        ),
        (
            "/v1/studies/STA-mini/raw?path=input/hydro/hydro/inter-monthly-breakdown/fr",
            43,
            None,
        ),
        (
            "/v1/studies/STA-mini/raw?path=input/thermal/clusters/fr/list/05_nuclear/marginal-cost",
            42,
            None,
        ),
        (
            "/v1/studies/STA-mini/raw?path=input/links/fr/properties/it/hurdles-cost",
            False,
            None,
        ),
    ],
)
def test_sta_mini_input(
    storage_service, url: str, new: SUB_JSON, expected: Optional[SUB_JSON]
):
    assert_with_errors(
        storage_service=storage_service,
        url=url,
        new=new,
        expected=expected,
    )


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, new",
    [
        (
            "/v1/studies/STA-mini/raw?path=output/20201014-1430adq/about-the-study/parameters/general/horizon",
            2042,
        ),
        (
            "/v1/studies/STA-mini/raw?path=output/20201014-1422eco-hello/about-the-study/study/antares/author",
            "John Smith",
        ),
        (
            "/v1/studies/STA-mini/raw?path=output/20201014-1422eco-hello/info/general/version",
            42,
        ),
    ],
)
def test_sta_mini_output(storage_service, url: str, new: SUB_JSON):
    assert_with_errors(
        storage_service=storage_service,
        url=url,
        new=new,
    )
