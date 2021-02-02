from antarest.login.model import User, Password


def test_password():
    assert Password("pwd") == "pwd"
