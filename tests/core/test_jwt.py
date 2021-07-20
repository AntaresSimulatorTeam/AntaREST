from antarest.core.jwt import JWTUser, JWTGroup
from antarest.core.roles import RoleType
from antarest.login.model import Group, User


def test_is_site_admin():
    jwt = JWTUser(
        id=0,
        impersonator=0,
        type="users",
        groups=[JWTGroup(id="admin", name="admin", role=RoleType.ADMIN)],
    )
    assert jwt.is_site_admin()
    assert not JWTUser(
        id=0,
        impersonator=0,
        type="users",
    ).is_site_admin()


def test_is_group_admin():
    jwt = JWTUser(
        id=0,
        impersonator=0,
        type="users",
        groups=[JWTGroup(id="group", name="group", role=RoleType.ADMIN)],
    )
    assert jwt.is_group_admin(Group(id="group"))
    assert not JWTUser(
        id=0,
        impersonator=0,
        type="users",
    ).is_group_admin(Group(id="group"))


def test_is_himself():
    jwt = JWTUser(
        id=1,
        impersonator=0,
        type="users",
    )
    assert jwt.is_himself(User(id=1))
    assert not JWTUser(
        id=0,
        impersonator=0,
        type="users",
    ).is_himself(User(id=1))
