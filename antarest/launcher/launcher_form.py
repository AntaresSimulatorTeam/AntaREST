"""
Launcher Dialog Box Object Model
"""
from typing import List, NamedTuple, Union

from pydantic import BaseModel

from pydantic.types import PositiveFloat, PositiveInt


class Version(NamedTuple):
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
    def construct(cls, *args: Union[str, int]) -> "Version":
        """
        Constructs a Version instance from a variable number of arguments.

        If only one argument is provided, it is treated as a string and each
        character is parsed as a separate component of the version number.
        Any missing components are filled with zeros.

        Args:
            A variable number of arguments representing the version number.
            Each argument can be either a string or an integer.

        Returns:
            A new Version instance.

        Raises:
            TypeError: if the number of arguments is incorrect.

        Usage:
            >>> from antarest.launcher.launcher_form import Version

            >>> Version.construct()
            Version(major=0, minor=0, patch=0)

            >>> Version.construct(841)
            Version(major=8, minor=4, patch=1)
            >>> Version.construct(8, 4, 1)
            Version(major=8, minor=4, patch=1)

            >>> Version.construct(85)
            Version(major=8, minor=5, patch=0)
            >>> Version.construct("85")
            Version(major=8, minor=5, patch=0)
            >>> Version.construct("8", "5")
            Version(major=8, minor=5, patch=0)
        """
        if len(args) == 1:
            args = tuple(str(args[0]))
        parts = tuple(int(p) for p in args) + (0,) * (3 - len(args))
        return cls(*parts)

    def __str__(self) -> str:
        """Returns a string representation of the Version object."""
        return ".".join(map(str, self))

    def __format__(self, format_spec: str) -> str:
        """
        Returns a formatted string representation of the Version object.

        The `patch` component is ignored if nul.

        Args:
            format_spec:
                A string specifying the format of the output:
                "s" for the short format, or "d" for the dotted format.
                Default is "s" (no dot).

        Returns:
            A formatted string representing the version number.

        Usage:
            >>> from antarest.launcher.launcher_form import Version

            >>> v841 = Version.construct(8, 4, 1)
            >>> f"{v841:s}"
            '841'
            >>> f"v{v841:d}"
            'v8.4.1'

            >>> v850 = Version.construct(8, 5, 0)
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


class _CamelCaseModel(BaseModel):
    class Config:
        @classmethod
        def alias_generator(cls, string: str) -> str:
            v = "".join(word.capitalize() for word in string.split("_"))
            return v[0].lower() + v[1:] if v else ""

        allow_population_by_field_name = True


class XpansionConfig(_CamelCaseModel):
    """Specific configuration for Xpansion"""

    use_sensibility_analysis: bool = False
    selected_output: str = ""
    available_outputs: List[str] = []


class SelectedStudy(_CamelCaseModel):
    """Selected Study (uuid, name, version)"""

    uuid: str
    name: str
    version: str
    use_xpansion: bool = False
    xpansion_config: XpansionConfig


class NbrOfCores(PositiveInt):
    """Number of cores used by the simulator"""

    lt = 64


class AdvancedConfig(_CamelCaseModel):
    """Advanced configuration of the simulation"""

    auto_uncompress: bool = True
    use_xpress_solver: bool = False
    solver_version: str = ""


class AdequacyPatchConfig(_CamelCaseModel):
    """Specific configuration for Adequacy Patch"""

    use_non_linearized_adp: bool = False


class AntaresLauncherForm(_CamelCaseModel):
    """Antares' Simulation dialog box used to launch studies"""

    selected_studies: List[SelectedStudy]
    output_suffix = str
    simu_timeout: PositiveFloat
    nbr_of_cores: NbrOfCores
    advanced_config: AdvancedConfig
    use_adequacy_patch: bool = False
    adequacy_patch_config: AdequacyPatchConfig


if __name__ == "__main__":
    import uuid

    launcher = AntaresLauncherForm(
        selected_studies=[
            {
                "uuid": str(uuid.uuid4()),
                "name": "foo",
                "version": "850",
            }
        ],
        output_suffix="foo",
        simu_timeout=0.1,
        nbr_of_cores=1,
        advanced_config={},
        xpansion_config={},
        adequacy_patch_config={},
    )
    print(launcher.json(by_alias=True, indent=True))
