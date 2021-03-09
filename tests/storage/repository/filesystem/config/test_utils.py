import pytest

from antarest.storage.repository.filesystem.config.model import (
    transform_name_to_id,
)


def test_id_transform():
    assert transform_name_to_id("@é'rFf") == "rff"
    assert transform_name_to_id("t@é'rFf") == "t rff"
