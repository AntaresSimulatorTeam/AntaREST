from typing import NamedTuple, Union


class VersionInfo(NamedTuple):
    """
    Represents an Antares Solver or Study version.

    Attributes:
        major: The major version number.
        minor: The minor version number.
        patch: The patch version number.
    """

    major: int
    minor: int
    patch: int

    @classmethod
    def construct(cls, *args: Union[str, int]) -> "VersionInfo":
        """
        Constructs a VersionInfo instance from a variable number of arguments.

        If only one argument is provided, it is treated as a string and each
        character is parsed as a separate component of the version number.
        Any missing components are filled with zeros.

        Args:
            A variable number of arguments representing the version number.
            Each argument can be either a string or an integer.

        Returns:
            A new VersionInfo instance.

        Raises:
            TypeError: if the number of arguments is incorrect.

        Usage:
            >>> from antarest.launcher.version_info import VersionInfo

            >>> VersionInfo.construct()
            VersionInfo(major=0, minor=0, patch=0)

            >>> VersionInfo.construct(841)
            VersionInfo(major=8, minor=4, patch=1)
            >>> VersionInfo.construct(8, 4, 1)
            VersionInfo(major=8, minor=4, patch=1)

            >>> VersionInfo.construct(85)
            VersionInfo(major=8, minor=5, patch=0)
            >>> VersionInfo.construct("85")
            VersionInfo(major=8, minor=5, patch=0)
            >>> VersionInfo.construct("8", "5")
            VersionInfo(major=8, minor=5, patch=0)
        """
        if len(args) == 1:
            args = tuple(str(args[0]))
        parts = tuple(int(p) for p in args) + (0,) * (3 - len(args))
        return cls(*parts)

    def __str__(self) -> str:
        """Returns a string representation of the VersionInfo object."""
        return ".".join(map(str, self))

    def __format__(self, format_spec: str) -> str:
        """
        Returns a formatted string representation of the VersionInfo object.

        The `patch` component is ignored if nul.

        Args:
            format_spec:
                A string specifying the format of the output:
                "s" for the short format, or "d" for the dotted format.
                Default is "s" (no dot).

        Returns:
            A formatted string representing the version number.

        Usage:
            >>> from antarest.launcher.version_info import VersionInfo

            >>> v841 = VersionInfo.construct(8, 4, 1)
            >>> f"{v841:s}"
            '841'
            >>> f"v{v841:d}"
            'v8.4.1'

            >>> v850 = VersionInfo.construct(8, 5, 0)
            >>> f"{v850}"
            '85'
            >>> f"v{v850:d}"
            'v8.5'
        """
        # separator: "." => "d" (dotted), "" => "s" (short)
        separators = {"": "", "s": "", "d": "."}
        sep = separators[format_spec]
        values = self if self.patch else [self.major, self.minor]
        return sep.join(map(str, values))
