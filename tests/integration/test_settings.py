import json

import pytest

from api_iso_antares.antares_io import server


@pytest.mark.integration_test
def test_request():

    app = server.application.test_client()
    res = app.get("/api/simulations/settings/generaldata.ini/general/nbyears")
    assert json.loads(res.data) == 2
