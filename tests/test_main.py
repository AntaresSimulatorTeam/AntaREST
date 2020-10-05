from api_iso_antares.main import hello


def test_hello() -> None:

    assert "Hello, World Antares" == hello()
