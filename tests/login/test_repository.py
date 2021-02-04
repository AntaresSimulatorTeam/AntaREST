from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from antarest.common.config import Config
from antarest.common.dto import Base
from antarest.login.model import User, Role, Password
from antarest.login.repository import UserRepository


def test_cyclelife():
    engine = create_engine("sqlite:///:memory:", echo=True)
    Session = sessionmaker(bind=engine)

    Base.metadata.create_all(engine)

    repo = UserRepository(
        config=Config({"login": {"admin": {"pwd": "admin"}}}), db=Session()
    )
    a = User(name="a", role=Role.ADMIN, password=Password("a"))
    b = User(name="b", role=Role.ADMIN, password=Password("b"))

    repo.save(a)
    repo.save(b)
    assert b.id
    assert a == repo.get(a.id)
    assert a.password == "a"
    assert b == repo.get_by_name("b")

    repo.delete(a.id)
    assert repo.get(a.id) is None
