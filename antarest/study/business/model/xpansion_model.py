from typing import Optional

from pydantic import Field, field_validator, model_validator

from antarest.core.exceptions import (
    BadCandidateFormatError,
    CandidateNameIsEmpty,
    IllegalCharacterInNameError,
    WrongLinkFormatError,
)
from antarest.core.serde import AntaresBaseModel


class XpansionCandidateInternal(AntaresBaseModel):
    name: str
    link: str
    annual_cost_per_mw: float = Field(alias="annual-cost-per-mw", gt=0)
    unit_size: Optional[float] = Field(default=None, alias="unit-size", ge=0)
    max_units: Optional[int] = Field(default=None, alias="max-units", ge=0)
    max_investment: Optional[float] = Field(default=None, alias="max-investment", ge=0)
    already_installed_capacity: Optional[int] = Field(default=None, alias="already-installed-capacity", ge=0)
    # this is obsolete (replaced by direct/indirect)
    link_profile: Optional[str] = Field(default=None, alias="link-profile")
    # this is obsolete (replaced by direct/indirect)
    already_installed_link_profile: Optional[str] = Field(default=None, alias="already-installed-link-profile")
    direct_link_profile: Optional[str] = Field(default=None, alias="direct-link-profile")
    indirect_link_profile: Optional[str] = Field(default=None, alias="indirect-link-profile")
    already_installed_direct_link_profile: Optional[str] = Field(
        default=None, alias="already-installed-direct-link-profile"
    )
    already_installed_indirect_link_profile: Optional[str] = Field(
        default=None, alias="already-installed-indirect-link-profile"
    )


class XpansionCandidateDTO(AntaresBaseModel):  # todo: we should refactor this class as the fields are not in camel case
    name: str
    link: str
    annual_cost_per_mw: float = Field(alias="annual-cost-per-mw", gt=0)
    unit_size: Optional[float] = Field(default=None, alias="unit-size", ge=0)
    max_units: Optional[int] = Field(default=None, alias="max-units", ge=0)
    max_investment: Optional[float] = Field(default=None, alias="max-investment", ge=0)
    already_installed_capacity: Optional[int] = Field(default=None, alias="already-installed-capacity", ge=0)
    # this is obsolete (replaced by direct/indirect)
    link_profile: Optional[str] = Field(default=None, alias="link-profile")
    # this is obsolete (replaced by direct/indirect)
    already_installed_link_profile: Optional[str] = Field(default=None, alias="already-installed-link-profile")
    direct_link_profile: Optional[str] = Field(default=None, alias="direct-link-profile")
    indirect_link_profile: Optional[str] = Field(default=None, alias="indirect-link-profile")
    already_installed_direct_link_profile: Optional[str] = Field(
        default=None, alias="already-installed-direct-link-profile"
    )
    already_installed_indirect_link_profile: Optional[str] = Field(
        default=None, alias="already-installed-indirect-link-profile"
    )

    @model_validator(mode="after")
    def validate_model(self) -> "XpansionCandidateDTO":
        possible_format_1 = self.max_investment is None and (self.max_units is not None and self.unit_size is not None)
        possible_format_2 = self.max_investment is not None and (self.max_units is None and self.unit_size is None)

        if not (possible_format_1 or possible_format_2):
            raise BadCandidateFormatError(
                "The candidate is not well formatted."
                "\nIt should either contain max-investment or (max-units and unit-size)."
            )

        return self

    @field_validator("name", mode="before")
    def validate_name(cls, name: str) -> str:
        # The name is written directly inside the ini file so a specific check is performed here
        if name.strip() == "":
            raise CandidateNameIsEmpty()

        illegal_name_characters = [" ", "\n", "\t", "\r", "\f", "\v", "-", "+", "=", ":", "[", "]", "(", ")"]
        for char in name:
            if char in illegal_name_characters:
                raise IllegalCharacterInNameError(f"The character '{char}' is not allowed in the candidate name")

        return name

    @field_validator("link", mode="before")
    def validate_link(cls, link: str) -> str:
        if " - " not in link:
            raise WrongLinkFormatError(f"The link must be in the format 'area1 - area2'. Currently: {link}")
        return link

    def to_internal_model(self) -> XpansionCandidateInternal:
        return XpansionCandidateInternal.model_validate(self.model_dump(mode="json", by_alias=True))
