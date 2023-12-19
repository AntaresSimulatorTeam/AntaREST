import typing as t
from enum import Enum

from pydantic import BaseModel


class BindingConstraintFrequency(str, Enum):
    """
    Frequency of binding constraint

    - HOURLY: hourly time series with 8784 lines
    - DAILY: daily time series with 366 lines
    - WEEKLY: weekly time series with 366 lines (same as daily)

    Usage example:

    >>> bcf = BindingConstraintFrequency.HOURLY
    >>> bcf == "hourly"
    True
    >>> bcf = BindingConstraintFrequency.DAILY
    >>> "daily" == bcf
    True
    >>> bcf = BindingConstraintFrequency.WEEKLY
    >>> bcf != "daily"
    True
    """

    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"


class BindingConstraintDTO(BaseModel):
    id: str
    areas: t.Set[str]
    clusters: t.Set[str]
    time_step: BindingConstraintFrequency
