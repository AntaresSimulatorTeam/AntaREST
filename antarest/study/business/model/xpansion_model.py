# Copyright (c) 2025, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.
from typing import Any, MutableMapping, Optional, Sequence

from pydantic import Field, ValidationError, field_validator, model_validator

from antarest.core.serde import AntaresBaseModel
from antarest.study.business.all_optional_meta import all_optional_model
from antarest.study.business.enum_ignore_case import EnumIgnoreCase


class XpansionResourceFileType(EnumIgnoreCase):
    CAPACITIES = "capacities"
    WEIGHTS = "weights"
    CONSTRAINTS = "constraints"


class UcType(EnumIgnoreCase):
    EXPANSION_FAST = "expansion_fast"
    EXPANSION_ACCURATE = "expansion_accurate"


class Master(EnumIgnoreCase):
    INTEGER = "integer"
    RELAXED = "relaxed"


class Solver(EnumIgnoreCase):
    CBC = "Cbc"
    COIN = "Coin"
    XPRESS = "Xpress"


class XpansionSensitivitySettings(AntaresBaseModel):
    """
    A DTO representing the sensitivity analysis settings used for Xpansion.

    The sensitivity analysis is optional.

    Attributes:
        epsilon: Max deviation from optimum (€).
        projection: List of candidate names to project (the candidate names should be in "candidates.ini" file).
        capex: Whether to include CAPEX in the sensitivity analysis.
    """

    epsilon: float = Field(default=0, ge=0, description="Max deviation from optimum (€)")
    projection: list[str] = Field(default_factory=list, description="List of candidate names to project")
    capex: bool = Field(default=False, description="Whether to include capex in the sensitivity analysis")

    @field_validator("projection", mode="before")
    def projection_validation(cls, v: Optional[Sequence[str]]) -> Sequence[str]:
        return [] if v is None else v


class XpansionSettings(AntaresBaseModel, extra="ignore", validate_assignment=True, populate_by_name=True):
    """
    A data transfer object representing the general settings used for Xpansion.

    Attributes:
        optimality_gap: Tolerance on absolute gap for the solution.
        max_iteration: Maximum number of Benders iterations for the solver.
        uc_type: Unit-commitment type used by Antares for the solver.
        master: Resolution mode of the master problem for the solver.
        yearly_weights: Path of the Monte-Carlo weights file for the solution.
        additional_constraints: Path of the additional constraints file for the solution.
        relaxed_optimality_gap: Threshold to switch from relaxed to integer master.
        relative_gap: Tolerance on relative gap for the solution.
        batch_size: Amount of batches in the Benders decomposition.
        separation_parameter: The separation parameter used in the Benders decomposition.
        solver: The solver used to solve the master and the sub-problems in the Benders decomposition.
        timelimit: The timelimit (in seconds) of the Benders step.
        log_level: The severity of the solver's logs in range [0, 3].
        sensitivity_config: The sensitivity analysis configuration for Xpansion, if any.

    Raises:
        ValueError: If the `relaxed_optimality_gap` attribute is not a float
        or a string ending with "%" and a valid float.
        ValueError: If the `max_iteration` attribute is not a valid integer.
    """

    # https://antares-xpansion.readthedocs.io/en/stable/user-guide/get-started/settings-definition/#master
    master: Master = Field(default=Master.INTEGER, description="Master problem resolution mode")

    # https://antares-xpansion.readthedocs.io/en/stable/user-guide/get-started/settings-definition/#uc_type
    uc_type: UcType = Field(default=UcType.EXPANSION_FAST, description="Unit commitment type")

    # https://antares-xpansion.readthedocs.io/en/stable/user-guide/get-started/settings-definition/#optimality_gap
    optimality_gap: float = Field(default=1, ge=0, description="Absolute optimality gap (€)")

    # https://antares-xpansion.readthedocs.io/en/stable/user-guide/get-started/settings-definition/#relative_gap
    relative_gap: float = Field(default=1e-6, ge=0, description="Relative optimality gap")

    # https://antares-xpansion.readthedocs.io/en/stable/user-guide/get-started/settings-definition/#relaxed_optimality_gap
    relaxed_optimality_gap: float = Field(default=1e-5, ge=0, description="Relative optimality gap for relaxation")

    # https://antares-xpansion.readthedocs.io/en/stable/user-guide/get-started/settings-definition/#max_iteration
    max_iteration: int = Field(default=1000, gt=0, description="Maximum number of iterations")

    # https://antares-xpansion.readthedocs.io/en/stable/user-guide/get-started/settings-definition/#solver
    solver: Solver = Field(default=Solver.XPRESS, description="Solver")

    # https://antares-xpansion.readthedocs.io/en/stable/user-guide/get-started/settings-definition/#log_level
    log_level: int = Field(default=0, ge=0, le=3, description="Log level in range [0, 3]")

    # https://antares-xpansion.readthedocs.io/en/stable/user-guide/get-started/settings-definition/#separation_parameter
    separation_parameter: float = Field(default=0.5, gt=0, le=1, description="Separation parameter in range ]0, 1]")

    # https://antares-xpansion.readthedocs.io/en/stable/user-guide/get-started/settings-definition/#batch_size
    batch_size: int = Field(default=96, ge=0, description="Number of batches")

    yearly_weights: str = Field(
        "",
        alias="yearly-weights",
        description="Yearly weights file",
    )
    additional_constraints: str = Field(
        "",
        alias="additional-constraints",
        description="Additional constraints file",
    )

    # (deprecated field)
    timelimit: int = int(1e12)

    # The sensitivity analysis is optional
    sensitivity_config: Optional[XpansionSensitivitySettings] = None

    @model_validator(mode="before")
    def validate_float_values(cls, values: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
        if "relaxed-optimality-gap" in values:
            values["relaxed_optimality_gap"] = values.pop("relaxed-optimality-gap")

        relaxed_optimality_gap = values.get("relaxed_optimality_gap")
        if relaxed_optimality_gap and isinstance(relaxed_optimality_gap, str):
            relaxed_optimality_gap = relaxed_optimality_gap.strip()
            if relaxed_optimality_gap.endswith("%"):
                # Don't divide by 100, because the value is already a percentage.
                values["relaxed_optimality_gap"] = float(relaxed_optimality_gap[:-1])
            else:
                values["relaxed_optimality_gap"] = float(relaxed_optimality_gap)

        separation_parameter = values.get("separation_parameter")
        if separation_parameter and isinstance(separation_parameter, str):
            separation_parameter = separation_parameter.strip()
            if separation_parameter.endswith("%"):
                values["separation_parameter"] = float(separation_parameter[:-1]) / 100
            else:
                values["separation_parameter"] = float(separation_parameter)

        if "max_iteration" in values:
            max_iteration = float(values["max_iteration"])
            if max_iteration == float("inf"):
                values["max_iteration"] = 1000

        return values


class GetXpansionSettings(XpansionSettings):
    """
    DTO object used to get the Xpansion settings.
    """

    @classmethod
    def from_config(cls, config_obj: dict[str, Any]) -> "GetXpansionSettings":
        """
        Create a GetXpansionSettings object from a JSON object.

        First, make an attempt to validate the JSON object.
        If it fails, try to read the settings without validation,
        so that the user can fix the issue in the form.

        Args:
            config_obj: The JSON object to read.

        Returns:
            The object which may contains extra attributes or invalid values.
        """
        try:
            return cls(**config_obj)
        except ValidationError:
            return cls.model_construct(**config_obj)


@all_optional_model
class UpdateXpansionSettings(XpansionSettings):
    """
    DTO object used to update the Xpansion settings.

    Fields with a value of `None` are ignored, this allows a partial update of the settings.
    For that reason the fields "yearly-weights" and "additional-constraints" must
    be set to "" instead of `None` if you want to remove the file.
    """

    # note: for some reason, the alias is not taken into account when using the metaclass,
    # so we have to redefine the fields with the alias.
    yearly_weights: str = Field(
        "",
        alias="yearly-weights",
        description="Yearly weights file",
    )

    additional_constraints: str = Field(
        "",
        alias="additional-constraints",
        description="Additional constraints file",
    )
