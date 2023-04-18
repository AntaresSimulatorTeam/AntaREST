"""
Launcher Dialog Box Object Model
"""
from typing import Any, Dict, List, Type

from antarest.launcher.version_info import VersionInfo
from pydantic import BaseModel as PydanticBaseModel
from pydantic import Extra, Field, root_validator, validator


class BaseModel(PydanticBaseModel):
    class Config:
        @classmethod
        def alias_generator(cls, string: str) -> str:
            v = "".join(word.capitalize() for word in string.split("_"))
            return v[0].lower() + v[1:] if v else ""

        allow_population_by_field_name = True
        extra = Extra.forbid


class XpansionConfig(BaseModel):
    """Specific configuration for Xpansion"""

    use_sensibility_analysis: bool = False
    selected_output: str = ""
    available_outputs: List[str] = Field(
        default_factory=list, unique_items=True
    )

    # noinspection PyMethodParameters
    @root_validator(pre=True)
    def validate_form(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if values.get("use_sensibility_analysis", False):
            if not (available_outputs := values.get("available_outputs", [])):
                raise ValueError(
                    "At least one simulation output is required"
                    " to use Xpansion with sensibility analysis"
                )
            available_outputs.sort(reverse=True)
            selected_output: bool = values.get("selected_output", "")
            if not selected_output:
                values["selected_output"] = available_outputs[0]
        return values

    class Config:
        @staticmethod
        def schema_extra(
            schema: Dict[str, Any], model: Type["XpansionConfig"]
        ) -> None:
            schema["example"] = model(
                use_sensibility_analysis=True,
                selected_output="2023-04-19_out3",
                available_outputs=[
                    "2023-04-18_out2",
                    "2023-04-19_out3",
                    "2023-04-17_out1",
                ],
            ).dict(by_alias=True)


class AdequacyPatchConfig(BaseModel):
    """Specific configuration for Adequacy Patch"""

    use_non_linearized_adp: bool = False


class SelectedStudy(XpansionConfig, AdequacyPatchConfig, BaseModel):
    """Selected Study (uuid, name, version)"""

    uuid: str
    name: str
    version: str
    use_xpansion: bool = False
    use_adequacy_patch: bool = False

    # noinspection PyMethodParameters
    @validator("version")
    def validate_version(cls, version: str) -> str:
        VersionInfo.construct(version)
        return version

    class Config:
        @staticmethod
        def schema_extra(
            schema: Dict[str, Any], model: Type["SelectedStudy"]
        ) -> None:
            schema["example"] = model(
                uuid="2f74a451-ddad-4ca4-a7c2-d3931f005b4a",
                name="foo",
                version="850",
                use_xpansion=True,
                use_sensibility_analysis=False,
                selected_output="",
                use_adequacy_patch=True,
                use_non_linearized_adp=True,
            ).dict(by_alias=True)


class AdvancedConfig(BaseModel):
    """Advanced configuration of the simulation"""

    auto_uncompress: bool = True
    use_xpress_solver: bool = False
    solver_version: str

    # noinspection PyMethodParameters
    @validator("solver_version")
    def validate_version(cls, solver_version: str) -> str:
        VersionInfo.construct(solver_version)
        return solver_version


class AntaresLauncherForm(AdvancedConfig, BaseModel):
    """Antares' Simulation dialog box used to launch studies"""

    selected_studies: List[SelectedStudy]
    output_suffix: str
    simu_timeout: float = Field(..., gt=0)  # type: ignore
    nbr_of_cores: int = Field(..., lt=64)  # type: ignore

    # noinspection PyMethodParameters
    @root_validator()
    def validate_versions(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        # fmt: off
        selected_studies: List[SelectedStudy] = values.get("selected_studies", [])
        solver_version = VersionInfo.construct(values.get("solver_version", ""))
        # fmt: on
        for study in selected_studies:
            version = VersionInfo.construct(study.version)
            if version > solver_version:
                raise ValueError(
                    f"Can't use Antares Solver v{solver_version:d}"
                    f" with study '{study.name}' in v{version:d},"
                    f" you must use a more recent Solver version."
                )
        return values


if __name__ == "__main__":
    import uuid

    launcher = AntaresLauncherForm(
        selected_studies=[
            SelectedStudy(
                uuid=str(uuid.uuid4()),
                name="foo",
                version="850",
                use_xpansion=False,
                use_adequacy_patch=True,
                use_non_linearized_adp=True,
            ),
            SelectedStudy(
                uuid=str(uuid.uuid4()),
                name="bar",
                version="840",
                use_xpansion=True,
                use_sensibility_analysis=True,
                selected_output="",
                available_outputs=[
                    "2023-04-18_out2",
                    "2023-04-19_out3",
                    "2023-04-17_out1",
                ],
                use_adequacy_patch=False,
            ),
        ],
        output_suffix="foo",
        simu_timeout=0.1,
        nbr_of_cores=1,
        solver_version="850",
    )
    print(launcher.json(by_alias=True, indent=True))
