"""
Generic types definition
"""

from typing import Callable, TypeAlias, TypeVar

T = TypeVar("T")

Supplier: TypeAlias = Callable[[], T]
