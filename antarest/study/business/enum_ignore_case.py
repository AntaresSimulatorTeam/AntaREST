import enum
import typing


class EnumIgnoreCase(str, enum.Enum):
    """
    Case-insensitive enum base class

    Usage:

    >>> class WeekDay(EnumIgnoreCase):
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
                # noinspection PyUnresolvedReferences
                if member.value.upper() == value.upper():
                    # noinspection PyTypeChecker
                    return member
        # `value` is not a valid
        return None
