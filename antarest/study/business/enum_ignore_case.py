import enum
import typing


class EnumIgnoreCase(enum.Enum):
    """
    Case-insensitive enum base class

    Usage:

    >>> class WeekDay(str, EnumIgnoreCase):
    ...     MONDAY = "Monday"
    ...     TUESDAY = "Tuesday"
    ...     WEDNESDAY = "Wednesday"
    ...     THURSDAY = "Thursday"
    ...     FRIDAY = "Friday"
    ...     SATURDAY = "Saturday"
    ...     SUNDAY = "Sunday"
    >>> WeekDay("monday")
    <WeekDay.MONDAY: 'Monday'>
    >>> WeekDay("MONDAY")
    <WeekDay.MONDAY: 'Monday'>
    """

    @classmethod
    def _missing_(cls, value: object) -> typing.Optional["EnumIgnoreCase"]:
        if isinstance(value, str):
            for member in cls:
                if member.value.upper() == value.upper():
                    return member
        # `value` is not a valid
        return None
