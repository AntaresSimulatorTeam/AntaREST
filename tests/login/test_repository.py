from antarest.login.model import User
from antarest.login.repository import UserRepository


def test_cyclelife():
    repo = UserRepository()
    a = User(id=0, name="a", pwd="a")
    b = User(name="b", pwd="b")

    repo.save(a)
    b = repo.save(b)
    assert b.id
    assert a == repo.get(0)
    assert b == repo.get_by_name("b")

    repo.delete(0)
    assert repo.get(0) is None
