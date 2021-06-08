import pytest

from antarest.common.custom_types import SUB_JSON
from antarest.common.jwt import JWTUser, JWTGroup
from antarest.common.roles import RoleType
from antarest.storage.service import StorageService
from antarest.common.requests import (
    RequestParameters,
)
from tests.storage.integration.data.de_details_hourly import de_details_hourly

ADMIN = JWTUser(
    id=1,
    impersonator=1,
    type="users",
    groups=[JWTGroup(id="admin", name="admin", role=RoleType.ADMIN)],
)


def assert_with_errors(
    storage_service: StorageService, url: str, new: SUB_JSON
) -> None:
    url = url[len("/v1/studies/") :]
    uuid, url = url.split("/raw?path=")
    params = RequestParameters(user=ADMIN)
    res = storage_service.edit_study(
        uuid=uuid, url=url, new=new, params=params
    )
    assert res == new

    res = storage_service.get(uuid=uuid, url=url, depth=-1, params=params)
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
    "url, new",
    [
        (
            "/v1/studies/STA-mini/raw?path=input/bindingconstraints/bindingconstraints",
            {},
        ),
        (
            "/v1/studies/STA-mini/raw?path=input/areas/sets/all areas/output",
            True,
        ),
        (
            "/v1/studies/STA-mini/raw?path=input/areas/de/optimization/nodal optimization/spread-spilled-energy-cost",
            42,
        ),
        ("/v1/studies/STA-mini/raw?path=input/areas/de/ui/layerX/0", 42),
        (
            "/v1/studies/STA-mini/raw?path=input/hydro/allocation/de/[allocation/de",
            42,
        ),
        (
            "/v1/studies/STA-mini/raw?path=input/load/prepro/fr/k",
            "write something",
        ),
        (
            "/v1/studies/STA-mini/raw?path=input/load/prepro/fr/k",
            "",
        ),
        (
            "/v1/studies/STA-mini/raw?path=input/load/series/load_fr",
            {
                "columns": [0],
                "index": list(range(100)),
                "data": [[i] for i in range(100)],
            },
        ),
        (
            "/v1/studies/STA-mini/raw?path=input/hydro/prepro/correlation/general/mode",
            "hourly",
        ),
        (
            "/v1/studies/STA-mini/raw?path=input/hydro/prepro/fr/prepro/prepro/intermonthly-correlation",
            0.42,
        ),
        (
            "/v1/studies/STA-mini/raw?path=input/hydro/hydro/inter-monthly-breakdown/fr",
            43,
        ),
        (
            "/v1/studies/STA-mini/raw?path=input/thermal/clusters/fr/list/05_nuclear/marginal-cost",
            42,
        ),
        (
            "/v1/studies/STA-mini/raw?path=input/links/fr/properties/it/hurdles-cost",
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
            "/v1/studies/STA-mini/raw?path=output/4/about-the-study/parameters/general/horizon",
            2042,
        ),
        (
            "/v1/studies/STA-mini/raw?path=output/1/about-the-study/study/antares/author",
            "John Smith",
        ),
        (
            "/v1/studies/STA-mini/raw?path=output/1/info/general/version",
            42,
        ),
        (
            "/v1/studies/STA-mini/raw?path=output/4/simulation-comments",
            "write something",
        ),
        (
            "/v1/studies/STA-mini/raw?path=output/1/economy/mc-ind/00001/areas/de/details-annual",
            de_details_hourly,
        ),
    ],
)
def test_sta_mini_output(storage_service, url: str, new: SUB_JSON):
    assert_with_errors(
        storage_service=storage_service,
        url=url,
        new=new,
    )
