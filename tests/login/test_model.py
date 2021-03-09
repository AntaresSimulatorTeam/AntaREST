from antarest.login.model import Password


def test_password():
    assert Password("pwd").check("pwd")
