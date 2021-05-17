from flask import Flask


def test_test(app: Flask):
    client = app.test_client()
    res = client.get("/auth")
    assert res is not None
