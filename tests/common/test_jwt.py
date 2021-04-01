from antarest.common.jwt import JWTUser, JWTGroup
from antarest.common.roles import RoleType
from antarest.login.model import Group, User


def test_is_site_admin():
    jwt = JWTUser(
        id=0, groups=[JWTGroup(id="admin", name="admin", role=RoleType.ADMIN)]
    )
    assert jwt.is_site_admin()
    assert not JWTUser(id=0).is_site_admin()


def test_is_group_admin():
    jwt = JWTUser(
        id=0, groups=[JWTGroup(id="group", name="group", role=RoleType.ADMIN)]
    )
    assert jwt.is_group_admin(Group(id="group"))
    assert not JWTUser(id=0).is_group_admin(Group(id="group"))


def test_is_himself():
    jwt = JWTUser(id=1)
    assert jwt.is_himself(User(id=1))
    assert not JWTUser(id=0).is_himself(User(id=1))
