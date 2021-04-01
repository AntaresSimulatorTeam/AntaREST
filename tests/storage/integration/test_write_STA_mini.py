import json

import pytest
from flask import Flask

from antarest.common.custom_types import SUB_JSON
from antarest.common.jwt import JWTUser, JWTGroup
from antarest.common.roles import RoleType
from antarest.storage.main import build_storage
from antarest.storage.service import StorageService
from antarest.common.requests import (
    RequestParameters,
)


ADMIN = JWTUser(
    id=1,
    name="admin",
    groups=[JWTGroup(id="admin", name="admin", role=RoleType.ADMIN)],
)


def assert_with_errors(
    storage_service: StorageService, url: str, new: SUB_JSON
) -> None:
    url = url[len("/studies/") :]
    print(url)
    params = RequestParameters(user=ADMIN)
    res = storage_service.edit_study(route=url, new=new, params=params)
    assert res == new

    res = storage_service.get(route=url, depth=-1, params=params)
    assert res == new


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, new",
    [
        ("/studies/STA-mini/settings/generaldata/general/horizon", 3000),
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
            "/studies/STA-mini/layers/layers/activeLayer/showAllLayer",
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
            "/studies/STA-mini/layers/layers/activeLayer/showAllLayer",
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
            "/studies/STA-mini/Desktop/.shellclassinfo",
            {
                "iconfile": "This is a test",
                "iconindex": 42,
                "infotip": "Hello",
            },
        ),
        ("/studies/STA-mini/Desktop/.shellclassinfo/iconindex", 42),
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
            "/studies/STA-mini/study/antares/created",
            42,
        ),
        (
            "/studies/STA-mini/study/antares/author",
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
    "url, new",
    [
        (
            "/studies/STA-mini/input/bindingconstraints/bindingconstraints",
            {},
        ),
        ("/studies/STA-mini/input/areas/sets/all areas/output", True),
        (
            "/studies/STA-mini/input/areas/de/optimization/nodal optimization/spread-spilled-energy-cost",
            42,
        ),
        ("/studies/STA-mini/input/areas/de/ui/layerX/0", 42),
        ("/studies/STA-mini/input/hydro/allocation/de/[allocation/de", 42),
        (
            "/studies/STA-mini/input/hydro/prepro/correlation/general/mode",
            "hourly",
        ),
        (
            "/studies/STA-mini/input/hydro/prepro/fr/prepro/prepro/intermonthly-correlation",
            0.42,
        ),
        (
            "/studies/STA-mini/input/hydro/hydro/inter-monthly-breakdown/fr",
            43,
        ),
        (
            "/studies/STA-mini/input/thermal/clusters/fr/list/05_nuclear/marginal-cost",
            42,
        ),
        (
            "/studies/STA-mini/input/links/fr/properties/it/hurdles-cost",
            False,
        ),
    ],
)
def test_sta_mini_input(storage_service, url: str, new: SUB_JSON):
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
            "/studies/STA-mini/output/4/about-the-study/parameters/general/horizon",
            2042,
        ),
        (
            "/studies/STA-mini/output/1/about-the-study/study/antares/author",
            "John Smith",
        ),
        (
            "/studies/STA-mini/output/1/info/general/version",
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
