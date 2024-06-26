"""
Object model used to read and update binding constraint configuration.
"""

from antarest.study.business.enum_ignore_case import EnumIgnoreCase


class BindingConstraintFrequency(EnumIgnoreCase):
    """
    Frequency of a binding constraint.

    Attributes:
        HOURLY: hourly time series with 8784 lines
        DAILY: daily time series with 366 lines
        WEEKLY: weekly time series with 366 lines (same as daily)
    """

    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"


class BindingConstraintOperator(EnumIgnoreCase):
    """
    Operator of a binding constraint.

    Attributes:
        LESS: less than or equal to
        GREATER: greater than or equal to
        BOTH: both LESS and GREATER
        EQUAL: equal to
    """

    LESS = "less"
    GREATER = "greater"
    BOTH = "both"
    EQUAL = "equal"
