from typing import Optional

import pytest

from antarest.core.custom_types import SUB_JSON
from antarest.core.jwt import JWTUser, JWTGroup
from antarest.core.roles import RoleType
from antarest.study.service import StudyService
from antarest.core.requests import (
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
            "/v1/studies/STA-mini/raw?path=input/hydro/allocation/de/[allocation/de",
            42,
            None,
        ),
        (
            "/v1/studies/STA-mini/raw?path=input/load/prepro/fr/k",
            b"write something",
            None,
        ),
        ("/v1/studies/STA-mini/raw?path=input/load/prepro/fr/k", b"", None),
        (
            "/v1/studies/STA-mini/raw?path=input/load/series/load_fr",
            {
                "columns": [0],
                "index": list(range(100)),
                "data": [[i] for i in range(100)],
            },
            None,
        ),
        (
            "/v1/studies/STA-mini/raw?path=input/load/series/load_fr",
            b"0\n1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n11\n12\n13\n14\n15\n16\n17\n18\n19\n20\n21\n22\n23\n24\n25\n26\n27\n28\n29\n30\n31\n32\n33\n34\n35\n36\n37\n38\n39\n40\n41\n42\n43\n44\n45\n46\n47\n48\n49\n50\n51\n52\n53\n54\n55\n56\n57\n58\n59\n60\n61\n62\n63\n64\n65\n66\n67\n68\n69\n70\n71\n72\n73\n74\n75\n76\n77\n78\n79\n80\n81\n82\n83\n84\n85\n86\n87\n88\n89\n90\n91\n92\n93\n94\n95\n96\n97\n98\n99\n",
            {
                "columns": [0],
                "index": list(range(100)),
                "data": [[i] for i in range(100)],
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
        (
            "/v1/studies/STA-mini/raw?path=output/20201014-1430adq/simulation-comments",
            b"write something",
        ),
        (
            "/v1/studies/STA-mini/raw?path=output/20201014-1422eco-hello/economy/mc-ind/00001/areas/de/details-annual",
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
