from typing import Tuple

import pytest

from antarest.storage.web.html_exception import (
    HtmlException,
    stop_and_return_on_html_exception,
)


@pytest.mark.unit_test
def test_stop_and_return_on_html_exception() -> None:
    @stop_and_return_on_html_exception
    def raise_html_exception(value: int) -> Tuple[str, int]:
        if value % 2:
            raise HtmlException("ex1", 1)
        return "ex2"

    message = raise_html_exception(0)
    assert message == "ex2"
    message, code_error = raise_html_exception(1)
    assert code_error == 1
