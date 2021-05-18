import time
import logging

from flask import Flask


def test_main(app: Flask):
    client = app.test_client()

    res = client.post("/login", data=dict(username="admin", password="admin"))
    admin_credentials = res.json

    # check default study presence
    time.sleep(2)
    res = client.get(
        "/studies",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert len(res.json) == 1

    # create some new users
    # TODO check for bad username or empty password
    res = client.post(
        "/users",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json={"name": "George", "password": "mypass"},
    )
    res = client.post(
        "/users",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json={"name": "Fred", "password": "mypass"},
    )
    res = client.post(
        "/users",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json={"name": "Harry", "password": "mypass"},
    )
    res = client.get(
        "/users",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert len(res.json) == 4

    # reject user with existing name creation
    res = client.post(
        "/users",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json={"name": "George", "password": "mypass"},
    )
    assert res.status_code == 400

    # login with new user
    # TODO mock ldap connector and test user login
    res = client.post(
        "/login", data=dict(username="George", password="mypass")
    )
    george_credentials = res.json
    res = client.post("/login", data=dict(username="Fred", password="mypass"))
    fred_credentials = res.json
    res = client.post("/login", data=dict(username="Harry", password="mypass"))
    harry_credentials = res.json

    # reject user creation from non admin
    res = client.post(
        "/users",
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
        json={"name": "Fred", "password": "mypass"},
    )
    assert res.status_code == 403

    # check study listing
    res = client.get(
        "/studies",
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
    )
    assert len(res.json) == 1

    # study creation
    res = client.post(
        "/studies/foo",
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
    )
    res = client.get(
        "/studies",
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
    )
    assert len(res.json) == 2

    # check study permission
    res = client.get(
        "/studies",
        headers={
            "Authorization": f'Bearer {fred_credentials["access_token"]}'
        },
    )
    assert len(res.json) == 1

    # play with groups
    res = client.post(
        "/groups",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json={"name": "Weasley"},
    )
    res = client.get(
        "/groups",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    group_id = res.json[1]["id"]
    res = client.post(
        "/roles",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json={"type": 40, "group_id": group_id, "identity_id": 3},
    )
    res = client.post(
        "/roles",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json={"type": 20, "group_id": group_id, "identity_id": 2},
    )
    # reset login to update credentials
    res = client.post(
        "/login", data=dict(username="George", password="mypass")
    )
    george_credentials = res.json
    res = client.post("/login", data=dict(username="Fred", password="mypass"))
    fred_credentials = res.json
    res = client.post(
        "/studies/bar",
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
    )
    res = client.get(
        "/studies",
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
    )
    assert len(res.json) == 3
    res = client.get(
        "/studies",
        headers={
            "Authorization": f'Bearer {fred_credentials["access_token"]}'
        },
    )
    assert len(res.json) == 2
