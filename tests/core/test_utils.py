import pytest

from antarest.core.exceptions import ShouldNotHappenException
from antarest.core.utils.utils import retry


def test_retry():
    def func_failure() -> str:
        raise ShouldNotHappenException()

    with pytest.raises(ShouldNotHappenException):
        retry(func_failure, 2)
