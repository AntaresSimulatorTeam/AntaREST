from antarest.common.swagger import _update


def test_update():
    swagger = {
        "swagger": "2.0",
        "info": {},
        "paths": {
            "/studies/{uuid}/{path}": {"post": {}},
            "/studies": {"post": {}},
            "/file/{path}": {"post": {}},
            "/studies/{path}": {
                "get": {"parameters": {1: {}}},
                "post": {"parameters": {1: {}}},
            },
        },
    }

    res = _update(swagger)
    assert "requestBody" in res["paths"]["/studies/{uuid}/{path}"]["post"]
    assert "requestBody" in res["paths"]["/studies"]["post"]
    assert "requestBody" in res["paths"]["/file/{path}"]["post"]
    assert "/studies/{uuid}/{path}" in res["paths"]
