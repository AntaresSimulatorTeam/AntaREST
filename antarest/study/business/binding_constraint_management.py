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

import collections
import copy
import logging
import typing as t

import numpy as np
from antares.study.version import StudyVersion
from pydantic import Field, field_validator, model_validator

from antarest.core.exceptions import (
    BindingConstraintNotFound,
    ConstraintTermNotFound,
    DuplicateConstraintName,
    DuplicateConstraintTerm,
    InvalidConstraintName,
    InvalidConstraintTerm,
    InvalidFieldForVersionError,
    MatrixWidthMismatchError,
    WrongMatrixHeightError,
)
from antarest.core.model import JSON
from antarest.core.requests import CaseInsensitiveDict
from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_camel_case
from antarest.study.business.all_optional_meta import camel_case_model
from antarest.study.business.utils import execute_or_add_commands
from antarest.study.model import STUDY_VERSION_8_3, STUDY_VERSION_8_7, Study
from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import (
    DEFAULT_GROUP,
    DEFAULT_OPERATOR,
    DEFAULT_TIMESTEP,
    BindingConstraintFrequency,
    BindingConstraintOperator,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.business.matrix_constants.binding_constraint.series_after_v87 import (
    default_bc_hourly as default_bc_hourly_87,
)
from antarest.study.storage.variantstudy.business.matrix_constants.binding_constraint.series_after_v87 import (
    default_bc_weekly_daily as default_bc_weekly_daily_87,
)
from antarest.study.storage.variantstudy.business.matrix_constants.binding_constraint.series_before_v87 import (
    default_bc_hourly as default_bc_hourly_86,
)
from antarest.study.storage.variantstudy.business.matrix_constants.binding_constraint.series_before_v87 import (
    default_bc_weekly_daily as default_bc_weekly_daily_86,
)
from antarest.study.storage.variantstudy.model.command.create_binding_constraint import (
    EXPECTED_MATRIX_SHAPES,
    BindingConstraintMatrices,
    BindingConstraintPropertiesBase,
    CreateBindingConstraint,
    OptionalProperties,
    TermMatrices,
    create_binding_constraint_config,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.remove_binding_constraint import RemoveBindingConstraint
from antarest.study.storage.variantstudy.model.command.remove_multiple_binding_constraints import (
    RemoveMultipleBindingConstraints,
)
from antarest.study.storage.variantstudy.model.command.replace_matrix import ReplaceMatrix
from antarest.study.storage.variantstudy.model.command.update_binding_constraint import (
    UpdateBindingConstraint,
    update_matrices_names,
)
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy

logger = logging.getLogger(__name__)


OPERATOR_CONFLICT_MAP = {
    BindingConstraintOperator.EQUAL: [TermMatrices.LESS.value, TermMatrices.GREATER.value],
    BindingConstraintOperator.GREATER: [TermMatrices.LESS.value, TermMatrices.EQUAL.value],
    BindingConstraintOperator.LESS: [TermMatrices.EQUAL.value, TermMatrices.GREATER.value],
    BindingConstraintOperator.BOTH: [TermMatrices.EQUAL.value],
}


class LinkTerm(AntaresBaseModel):
    """
    DTO for a constraint term on a link between two areas.

    Attributes:
        area1: the first area ID
        area2: the second area ID
    """

    area1: str
    area2: str

    def generate_id(self) -> str:
        """Return the constraint term ID for this link, of the form "area1%area2"."""
        # Ensure IDs are in alphabetical order and lower case
        ids = sorted((self.area1.lower(), self.area2.lower()))
        return "%".join(ids)


class ClusterTerm(AntaresBaseModel):
    """
    DTO for a constraint term on a cluster in an area.

    Attributes:
        area: the area ID
        cluster: the cluster ID
    """

    area: str
    cluster: str

    def generate_id(self) -> str:
        """Return the constraint term ID for this Area/cluster constraint, of the form "area.cluster"."""
        # Ensure IDs are in lower case
        ids = [self.area.lower(), self.cluster.lower()]
        return ".".join(ids)


class ConstraintTerm(AntaresBaseModel):
    """
    DTO for a constraint term.

    Attributes:
        id: the constraint term ID, of the form "area1%area2" or "area.cluster".
        weight: the constraint term weight, if any.
        offset: the constraint term offset, if any.
        data: the constraint term data (link or cluster), if any.
    """

    id: t.Optional[str] = None
    weight: t.Optional[float] = None
    offset: t.Optional[int] = None
    data: t.Optional[t.Union[LinkTerm, ClusterTerm]] = None

    @field_validator("id")
    def id_to_lower(cls, v: t.Optional[str]) -> t.Optional[str]:
        """Ensure the ID is lower case."""
        if v is None:
            return None
        return v.lower()

    def generate_id(self) -> str:
        """Return the constraint term ID for this term based on its data."""
        if self.data is None:
            return self.id or ""
        return self.data.generate_id()


class ConstraintFilters(AntaresBaseModel, frozen=True, extra="forbid"):
    """
    Binding Constraint Filters gathering the main filtering parameters.

    Attributes:
        bc_id: binding constraint ID (exact match)
        enabled: enabled status
        operator: operator
        comments: comments (word match, case-insensitive)
        group: on group name (exact match, case-insensitive)
        time_step: time step
        area_name: area name (word match, case-insensitive)
        cluster_name: cluster name (word match, case-insensitive)
        link_id: link ID ('area1%area2') in at least one term.
        cluster_id: cluster ID ('area.cluster') in at least one term.
    """

    bc_id: str = ""
    enabled: t.Optional[bool] = None
    operator: t.Optional[BindingConstraintOperator] = None
    comments: str = ""
    group: str = ""
    time_step: t.Optional[BindingConstraintFrequency] = None
    area_name: str = ""
    cluster_name: str = ""
    link_id: str = ""
    cluster_id: str = ""

    def match_filters(self, constraint: "ConstraintOutput") -> bool:
        """
        Check if the constraint matches the filters.

        Args:
            constraint: the constraint to check

        Returns:
            True if the constraint matches the filters, False otherwise
        """
        if self.bc_id and self.bc_id != constraint.id:
            # The `bc_id` filter is a case-sensitive exact match.
            return False
        if self.enabled is not None and self.enabled != constraint.enabled:
            return False
        if self.operator is not None and self.operator != constraint.operator:
            return False
        if self.comments:
            # The `comments` filter is a case-insensitive substring match.
            comments = constraint.comments or ""
            if self.comments.upper() not in comments.upper():
                return False
        if self.group:
            # The `group` filter is a case-insensitive exact match.
            group = getattr(constraint, "group", DEFAULT_GROUP)
            if self.group.upper() != group.upper():
                return False
        if self.time_step is not None and self.time_step != constraint.time_step:
            return False

        terms = constraint.terms or []

        if self.area_name:
            # The `area_name` filter is a case-insensitive substring match.
            area_name_upper = self.area_name.upper()
            for data in (term.data for term in terms if term.data):
                # fmt: off
                if (
                    isinstance(data, LinkTerm)
                    and (area_name_upper in data.area1.upper() or area_name_upper in data.area2.upper())
                ) or (
                    isinstance(data, ClusterTerm)
                    and area_name_upper in data.area.upper()
                ):
                    break
                # fmt: on
            else:
                return False

        if self.cluster_name:
            # The `cluster_name` filter is a case-insensitive substring match.
            cluster_name_upper = self.cluster_name.upper()
            for data in (term.data for term in terms if term.data):
                if isinstance(data, ClusterTerm) and cluster_name_upper in data.cluster.upper():
                    break
            else:
                return False

        if self.link_id:
            # The `link_id` filter is a case-insensitive exact match.
            all_link_ids = [term.data.generate_id() for term in terms if isinstance(term.data, LinkTerm)]
            if self.link_id.lower() not in all_link_ids:
                return False

        if self.cluster_id:
            # The `cluster_id` filter is a case-insensitive exact match.
            all_cluster_ids = [term.data.generate_id() for term in terms if isinstance(term.data, ClusterTerm)]
            if self.cluster_id.lower() not in all_cluster_ids:
                return False

        return True


@camel_case_model
class ConstraintInput870(OptionalProperties):
    pass


@camel_case_model
class ConstraintInput(BindingConstraintMatrices, ConstraintInput870):
    terms: t.MutableSequence[ConstraintTerm] = Field(
        default_factory=lambda: [],
    )


@camel_case_model
class ConstraintCreation(ConstraintInput):
    name: str

    @model_validator(mode="before")
    def check_matrices_dimensions(cls, values: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
        for _key in ["time_step"] + [m.value for m in TermMatrices]:
            _camel = to_camel_case(_key)
            values[_key] = values.pop(_camel, values.get(_key))

        # The dimensions of the matrices depend on the frequency and the version of the study.
        if values.get("time_step") is None:
            return values
        _time_step = BindingConstraintFrequency(values["time_step"])

        # Matrix shapes for binding constraints are different from usual shapes,
        # because we need to take leap years into account, which contains 366 days and 8784 hours.
        # Also, we use the same matrices for "weekly" and "daily" frequencies,
        # because the solver calculates the weekly matrix from the daily matrix.
        # See https://github.com/AntaresSimulatorTeam/AntaREST/issues/1843
        expected_rows = EXPECTED_MATRIX_SHAPES[_time_step][0]

        # Collect the matrix shapes
        matrix_shapes = {}
        for _field_name in ["values"] + [m.value for m in TermMatrices]:
            if _matrix := values.get(_field_name):
                _array = np.array(_matrix)
                # We only store the shape if the array is not empty
                if _array.size != 0:
                    matrix_shapes[_field_name] = _array.shape

        # We don't know the exact version of the study here, but we can rely on the matrix field names.
        if not matrix_shapes:
            return values
        elif "values" in matrix_shapes:
            expected_cols = 3
        else:
            # pick the first matrix column as the expected column
            expected_cols = next(iter(matrix_shapes.values()))[1]

        if all(shape == (expected_rows, expected_cols) for shape in matrix_shapes.values()):
            return values

        # Prepare a clear error message
        _field_names = ", ".join(f"'{n}'" for n in matrix_shapes)
        if len(matrix_shapes) == 1:
            err_msg = f"Matrix {_field_names} must have the shape ({expected_rows}, {expected_cols})"
        else:
            _shapes = list({(expected_rows, s[1]) for s in matrix_shapes.values()})
            _shapes_msg = ", ".join(f"{s}" for s in _shapes[:-1]) + " or " + f"{_shapes[-1]}"
            err_msg = f"Matrices {_field_names} must have the same shape: {_shapes_msg}"

        raise ValueError(err_msg)


class ConstraintOutputBase(BindingConstraintPropertiesBase):
    id: str
    name: str
    terms: t.MutableSequence[ConstraintTerm] = Field(default_factory=lambda: [])
    # I have to redefine the time_step attribute to give him another alias.
    time_step: t.Optional[BindingConstraintFrequency] = Field(DEFAULT_TIMESTEP, alias="timeStep")  # type: ignore


class ConstraintOutput830(ConstraintOutputBase):
    filter_year_by_year: str = Field(default="", alias="filterYearByYear")
    filter_synthesis: str = Field(default="", alias="filterSynthesis")


class ConstraintOutput870(ConstraintOutput830):
    group: str = DEFAULT_GROUP


# WARNING: Do not change the order of the following line, it is used to determine
# the type of the output constraint in the FastAPI endpoint.
ConstraintOutput = t.Union[ConstraintOutputBase, ConstraintOutput830, ConstraintOutput870]

OPERATOR_MATRIX_FILE_MAP = {
    BindingConstraintOperator.EQUAL: ["{bc_id}_eq"],
    BindingConstraintOperator.GREATER: ["{bc_id}_gt"],
    BindingConstraintOperator.LESS: ["{bc_id}_lt"],
    BindingConstraintOperator.BOTH: ["{bc_id}_lt", "{bc_id}_gt"],
}


def _get_references_by_widths(
    file_study: FileStudy, bcs: t.Sequence[ConstraintOutput]
) -> t.Mapping[int, t.Sequence[t.Tuple[str, str]]]:
    """
    Iterates over each BC and its associated matrices.
    For each matrix, it checks its width according to the expected matrix shapes.
    It then groups the binding constraints by these widths.

    Notes:
        The height of the matrices may vary depending on the time step,
        but the width should be consistent within a group of binding constraints.
    """

    references_by_width: t.Dict[int, t.List[t.Tuple[str, str]]] = {}
    _total = len(bcs)
    for _index, bc in enumerate(bcs):
        matrices_name = (
            OPERATOR_MATRIX_FILE_MAP[bc.operator] if file_study.config.version >= STUDY_VERSION_8_7 else ["{bc_id}"]
        )
        for matrix_name in matrices_name:
            matrix_id = matrix_name.format(bc_id=bc.id)
            logger.info(f"⏲ Validating BC '{bc.id}': {matrix_id=} [{_index+1}/{_total}]")
            obj = file_study.tree.get(url=["input", "bindingconstraints", matrix_id])
            matrix = np.array(obj["data"], dtype=float)
            # We ignore empty matrices as there are default matrices for the simulator.
            if not matrix.size:
                continue

            matrix_height = matrix.shape[0]
            expected_height = EXPECTED_MATRIX_SHAPES[bc.time_step][0]  # type: ignore
            if matrix_height != expected_height:
                raise WrongMatrixHeightError(
                    f"The binding constraint '{bc.name}' should have {expected_height} rows, currently: {matrix_height}"
                )
            matrix_width = matrix.shape[1]
            if matrix_width > 1:
                references_by_width.setdefault(matrix_width, []).append((bc.id, matrix_id))

    return references_by_width


def _generate_replace_matrix_commands(
    bc_id: str,
    study_version: StudyVersion,
    value: ConstraintInput,
    operator: BindingConstraintOperator,
    command_context: CommandContext,
) -> t.List[ICommand]:
    commands: t.List[ICommand] = []
    if study_version < STUDY_VERSION_8_7:
        matrix = {
            BindingConstraintFrequency.HOURLY.value: default_bc_hourly_86,
            BindingConstraintFrequency.DAILY.value: default_bc_weekly_daily_86,
            BindingConstraintFrequency.WEEKLY.value: default_bc_weekly_daily_86,
        }[value.time_step].tolist()
        command = ReplaceMatrix(
            target=f"input/bindingconstraints/{bc_id}",
            matrix=matrix,
            command_context=command_context,
            study_version=study_version,
        )
        commands.append(command)
    else:
        matrix = {
            BindingConstraintFrequency.HOURLY.value: default_bc_hourly_87,
            BindingConstraintFrequency.DAILY.value: default_bc_weekly_daily_87,
            BindingConstraintFrequency.WEEKLY.value: default_bc_weekly_daily_87,
        }[value.time_step].tolist()
        matrices_to_replace = OPERATOR_MATRIX_FILE_MAP[operator]
        for matrix_name in matrices_to_replace:
            matrix_id = matrix_name.format(bc_id=bc_id)
            command = ReplaceMatrix(
                target=f"input/bindingconstraints/{matrix_id}",
                matrix=matrix,
                command_context=command_context,
                study_version=study_version,
            )
            commands.append(command)
    return commands


def _validate_binding_constraints(file_study: FileStudy, bcs: t.Sequence[ConstraintOutput]) -> bool:
    """
    Validates the binding constraints within a group.
    """
    references_by_widths = _get_references_by_widths(file_study, bcs)

    if len(references_by_widths) > 1:
        most_common = collections.Counter(references_by_widths.keys()).most_common()
        invalid_constraints: t.Dict[str, str] = {}

        for width, _ in most_common[1:]:
            references = references_by_widths[width]
            for bc_id, matrix_id in references:
                existing_key = invalid_constraints.get(bc_id, "")
                if existing_key:
                    existing_key += ", "
                existing_key += f"'{matrix_id}' has {width} columns"
                invalid_constraints[bc_id] = existing_key

        expected_width = most_common[0][0]
        raise MatrixWidthMismatchError(
            f"Mismatch widths: the most common width in the group is {expected_width}"
            f" but we have: {invalid_constraints!r}"
        )

    return True


# noinspection SpellCheckingInspection
_ALL_BINDING_CONSTRAINTS_PATH = "input/bindingconstraints/bindingconstraints"


class BindingConstraintManager:
    def __init__(
        self,
        storage_service: StudyStorageService,
    ) -> None:
        self.storage_service = storage_service

    @staticmethod
    def parse_and_add_terms(key: str, value: t.Any, adapted_constraint: ConstraintOutput) -> None:
        """Parse a single term from the constraint dictionary and add it to the adapted_constraint model."""
        if "%" in key or "." in key:
            separator = "%" if "%" in key else "."
            term_data = key.split(separator)
            if isinstance(value, (float, int)):
                weight, offset = (float(value), None)
            else:
                _parts = value.partition("%")
                weight = float(_parts[0])
                offset = int(_parts[2]) if _parts[2] else None

            if separator == "%":
                # Link term
                adapted_constraint.terms.append(
                    ConstraintTerm(
                        id=key,
                        weight=weight,
                        offset=offset,
                        data=LinkTerm.model_validate(
                            {
                                "area1": term_data[0],
                                "area2": term_data[1],
                            }
                        ),
                    )
                )
            # Cluster term
            else:
                adapted_constraint.terms.append(
                    ConstraintTerm(
                        id=key,
                        weight=weight,
                        offset=offset,
                        data=ClusterTerm.model_validate({"area": term_data[0], "cluster": term_data[1]}),
                    )
                )

    @staticmethod
    def constraint_model_adapter(constraint: t.Mapping[str, t.Any], study_version: StudyVersion) -> ConstraintOutput:
        """
        Adapts a binding constraint configuration to the appropriate model version.

        Args:
            constraint: A dictionary or model representing the constraint to be adapted.
                This can either be a dictionary coming from client input or an existing
                model that needs reformatting.
            study_version: A StudyVersion object indicating the target version of the study configuration. This is used to
                determine which model class to instantiate and which default values to apply.

        Returns:
            A new instance of either `ConstraintOutputBase`, `ConstraintOutput830`, or `ConstraintOutput870`,
            populated with the adapted values from the input constraint, and conforming to the
            structure expected by the specified version.

        Note:
            This method is crucial for ensuring backward compatibility and future-proofing the application
            as it evolves. It allows client-side data to be accurately represented within the config and
            ensures data integrity when storing or retrieving constraint configurations from the database.
        """

        constraint_output = {
            "id": constraint["id"],
            "name": constraint["name"],
            "enabled": constraint.get("enabled", True),
            "time_step": constraint.get("type", DEFAULT_TIMESTEP),
            "operator": constraint.get("operator", DEFAULT_OPERATOR),
            "comments": constraint.get("comments", ""),
            "terms": constraint.get("terms", []),
        }

        if study_version >= STUDY_VERSION_8_3:
            _filter_year_by_year = constraint.get("filter_year_by_year") or constraint.get("filter-year-by-year", "")
            _filter_synthesis = constraint.get("filter_synthesis") or constraint.get("filter-synthesis", "")
            constraint_output["filter_year_by_year"] = _filter_year_by_year
            constraint_output["filter_synthesis"] = _filter_synthesis
        if study_version >= STUDY_VERSION_8_7:
            constraint_output["group"] = constraint.get("group", DEFAULT_GROUP)

        # Choose the right model according to the version
        adapted_constraint: ConstraintOutput
        if study_version >= STUDY_VERSION_8_7:
            adapted_constraint = ConstraintOutput870(**constraint_output)
        elif study_version >= STUDY_VERSION_8_3:
            adapted_constraint = ConstraintOutput830(**constraint_output)
        else:
            adapted_constraint = ConstraintOutputBase(**constraint_output)

        # If 'terms' were not directly provided in the input, parse and add terms dynamically
        if not constraint.get("terms"):
            for key, value in constraint.items():
                if key not in constraint_output:  # Avoid re-processing keys already included
                    BindingConstraintManager.parse_and_add_terms(key, value, adapted_constraint)

        return adapted_constraint

    @staticmethod
    def terms_to_coeffs(terms: t.Sequence[ConstraintTerm]) -> t.Dict[str, t.List[float]]:
        """
        Converts a sequence of terms into a dictionary mapping each term's ID to its coefficients,
        including the weight and, optionally, the offset.

        :param terms: A sequence of terms to be converted.
        :return: A dictionary of term IDs mapped to a list of their coefficients.
        """
        coeffs = {}
        for term in terms:
            if term.id and term.weight is not None:
                coeffs[term.id] = [term.weight]
                if term.offset:
                    coeffs[term.id].append(term.offset)
        return coeffs

    def check_binding_constraints_exists(self, study: Study, bc_ids: t.List[str]) -> None:
        storage_service = self.storage_service.get_storage(study)
        file_study = storage_service.get_raw(study)
        existing_constraints = file_study.tree.get(["input", "bindingconstraints", "bindingconstraints"])

        existing_ids = {constraint["id"] for constraint in existing_constraints.values()}

        missing_bc_ids = [bc_id for bc_id in bc_ids if bc_id not in existing_ids]

        if missing_bc_ids:
            raise BindingConstraintNotFound(f"Binding constraint(s) '{missing_bc_ids}' not found")

    def get_binding_constraint(self, study: Study, bc_id: str) -> ConstraintOutput:
        """
        Retrieves a binding constraint by its ID within a given study.

        Args:
            study: The study from which to retrieve the constraint.
            bc_id: The ID of the binding constraint to retrieve.

        Returns:
            A ConstraintOutput object representing the binding constraint with the specified ID.

        Raises:
            BindingConstraintNotFound: If no binding constraint with the specified ID is found.
        """
        storage_service = self.storage_service.get_storage(study)
        file_study = storage_service.get_raw(study)
        config = file_study.tree.get(["input", "bindingconstraints", "bindingconstraints"])

        constraints_by_id: t.Dict[str, ConstraintOutput] = CaseInsensitiveDict()  # type: ignore

        for constraint in config.values():
            constraint_config = self.constraint_model_adapter(constraint, StudyVersion.parse(study.version))
            constraints_by_id[constraint_config.id] = constraint_config

        if bc_id not in constraints_by_id:
            raise BindingConstraintNotFound(f"Binding constraint '{bc_id}' not found")

        return constraints_by_id[bc_id]

    def get_binding_constraints(
        self, study: Study, filters: ConstraintFilters = ConstraintFilters()
    ) -> t.Sequence[ConstraintOutput]:
        """
        Retrieves all binding constraints within a given study, optionally filtered by specific criteria.

        Args:
            study: The study from which to retrieve the constraints.
            filters: The filters to apply when retrieving the constraints.

        Returns:
            A list of ConstraintOutput objects representing the binding constraints that match the specified filters.
        """
        storage_service = self.storage_service.get_storage(study)
        file_study = storage_service.get_raw(study)
        config = file_study.tree.get(["input", "bindingconstraints", "bindingconstraints"])
        outputs = [self.constraint_model_adapter(c, StudyVersion.parse(study.version)) for c in config.values()]
        filtered_constraints = list(filter(lambda c: filters.match_filters(c), outputs))
        return filtered_constraints

    def get_grouped_constraints(self, study: Study) -> t.Mapping[str, t.Sequence[ConstraintOutput]]:
        """
         Retrieves and groups all binding constraints by their group names within a given study.

        This method organizes binding constraints into a dictionary where each key corresponds to a group name,
        and the value is a list of ConstraintOutput objects associated with that group.

        Args:
            study: the study

        Returns:
            A dictionary mapping group names to lists of binding constraints associated with each group.

        Notes:
        The grouping considers the exact group name, implying case sensitivity. If case-insensitive grouping
        is required, normalization of group names to a uniform case (e.g., all lower or upper) should be performed.
        """
        storage_service = self.storage_service.get_storage(study)
        file_study = storage_service.get_raw(study)
        config = file_study.tree.get(["input", "bindingconstraints", "bindingconstraints"])
        grouped_constraints = CaseInsensitiveDict()

        for constraint in config.values():
            constraint_config = self.constraint_model_adapter(constraint, StudyVersion.parse(study.version))
            constraint_group = getattr(constraint_config, "group", DEFAULT_GROUP)
            grouped_constraints.setdefault(constraint_group, []).append(constraint_config)

        return grouped_constraints

    def get_constraints_by_group(self, study: Study, group_name: str) -> t.Sequence[ConstraintOutput]:
        """
         Retrieve all binding constraints belonging to a specified group within a study.

        Args:
            study: The study from which to retrieve the constraints.
            group_name: The name of the group (case-insensitive).

        Returns:
            A list of ConstraintOutput objects that belong to the specified group.

        Raises:
            BindingConstraintNotFound: If the specified group name is not found among the constraint groups.
        """
        grouped_constraints = self.get_grouped_constraints(study)

        if group_name not in grouped_constraints:
            raise BindingConstraintNotFound(f"Group '{group_name}' not found")

        return grouped_constraints[group_name]

    def validate_constraint_group(self, study: Study, group_name: str) -> bool:
        """
        Validates if the specified group name exists within the study's binding constraints
        and checks the validity of the constraints within that group.

        This method performs a case-insensitive search to match the specified group name against
        existing groups of binding constraints. It ensures that the group exists and then
        validates the constraints within that found group.

        Args:
            study: The study object containing binding constraints.
            group_name: The name of the group (case-insensitive).

        Returns:
            True if the group exists and the constraints within the group are valid; False otherwise.

        Raises:
            BindingConstraintNotFound: If no matching group name is found in a case-insensitive manner.
        """
        storage_service = self.storage_service.get_storage(study)
        file_study = storage_service.get_raw(study)
        grouped_constraints = self.get_grouped_constraints(study)

        if group_name not in grouped_constraints:
            raise BindingConstraintNotFound(f"Group '{group_name}' not found")

        constraints = grouped_constraints[group_name]
        return _validate_binding_constraints(file_study, constraints)

    def validate_constraint_groups(self, study: Study) -> bool:
        """
        Validates all groups of binding constraints within the given study.

        This method checks each group of binding constraints for validity based on specific criteria
        (e.g., coherence between matrices lengths). If any group fails the validation, an aggregated
        error detailing all incoherence is raised.

        Args:
            study: The study object containing binding constraints.

        Returns:
            True if all constraint groups are valid.

        Raises:
            IncoherenceBetweenMatricesLength: If any validation checks fail.
        """
        storage_service = self.storage_service.get_storage(study)
        file_study = storage_service.get_raw(study)
        grouped_constraints = self.get_grouped_constraints(study)
        invalid_groups = {}

        for group_name, bcs in grouped_constraints.items():
            try:
                _validate_binding_constraints(file_study, bcs)
            except MatrixWidthMismatchError as e:
                invalid_groups[group_name] = e.detail

        if invalid_groups:
            err_msg = ", ".join(f"'{grp}': {msg}" for grp, msg in sorted(invalid_groups.items()))
            raise MatrixWidthMismatchError(err_msg)

        return True

    def create_binding_constraint(
        self,
        study: Study,
        data: ConstraintCreation,
    ) -> ConstraintOutput:
        bc_id = transform_name_to_id(data.name)
        version = StudyVersion.parse(study.version)

        if not bc_id:
            raise InvalidConstraintName(f"Invalid binding constraint name: {data.name}.")

        if bc_id in {bc.id for bc in self.get_binding_constraints(study)}:
            raise DuplicateConstraintName(f"A binding constraint with the same name already exists: {bc_id}.")

        check_attributes_coherence(data, version, data.operator or DEFAULT_OPERATOR)

        new_constraint = {
            "name": data.name,
            **data.model_dump(mode="json", exclude={"terms", "name"}, exclude_none=True),
        }
        args = {
            **new_constraint,
            "command_context": self.storage_service.variant_study_service.command_factory.command_context,
            "study_version": version,
        }
        if data.terms:
            args["coeffs"] = self.terms_to_coeffs(data.terms)

        command = CreateBindingConstraint(**args)

        # Validates the matrices. Needed when the study is a variant because we only append the command to the list
        if isinstance(study, VariantStudy):
            time_step = data.time_step or DEFAULT_TIMESTEP
            command.validates_and_fills_matrices(
                time_step=time_step, specific_matrices=None, version=version, create=True
            )

        file_study = self.storage_service.get_storage(study).get_raw(study)
        execute_or_add_commands(study, file_study, [command], self.storage_service)

        # Processes the constraints to add them inside the endpoint response.
        new_constraint["id"] = bc_id
        return self.constraint_model_adapter(new_constraint, version)

    def duplicate_binding_constraint(self, study: Study, source_id: str, new_constraint_name: str) -> ConstraintOutput:
        """
        Creates a duplicate constraint with a new name.

        Args:
            study: The study in which the cluster will be duplicated.
            source_id: The identifier of the constraint to be duplicated.
            new_constraint_name: The new name for the duplicated constraint.

        Returns:
            The duplicated constraint configuration.

        Raises:
            DuplicateConstraintName: If a constraint with the new name already exists in the study.
        """

        # Checks if the new constraint already exists
        new_constraint_id = transform_name_to_id(new_constraint_name)
        existing_constraints = self.get_binding_constraints(study)
        if new_constraint_id in {bc.id for bc in existing_constraints}:
            raise DuplicateConstraintName(
                f"A binding constraint with the same name already exists: {new_constraint_name}."
            )

        # Retrieval of the source constraint properties
        source_constraint = next(iter(bc for bc in existing_constraints if bc.id == source_id), None)
        if not source_constraint:
            raise BindingConstraintNotFound(f"Binding constraint '{source_id}' not found")

        new_constraint = {
            "name": new_constraint_name,
            **source_constraint.model_dump(mode="json", exclude={"terms", "name", "id"}),
        }
        args = {
            **new_constraint,
            "command_context": self.storage_service.variant_study_service.command_factory.command_context,
            "study_version": StudyVersion.parse(study.version),
        }
        if source_constraint.terms:
            args["coeffs"] = self.terms_to_coeffs(source_constraint.terms)

        # Retrieval of the source constraint matrices
        file_study = self.storage_service.get_storage(study).get_raw(study)
        if file_study.config.version < STUDY_VERSION_8_7:
            matrix = file_study.tree.get(["input", "bindingconstraints", source_id])
            args["values"] = matrix["data"]
        else:
            correspondence_map = {
                "lt": TermMatrices.LESS.value,
                "gt": TermMatrices.GREATER.value,
                "eq": TermMatrices.EQUAL.value,
            }
            source_matrices = OPERATOR_MATRIX_FILE_MAP[source_constraint.operator]
            for matrix_name in source_matrices:
                matrix = file_study.tree.get(["input", "bindingconstraints", matrix_name.format(bc_id=source_id)])[
                    "data"
                ]
                command_attribute = correspondence_map[matrix_name.removeprefix("{bc_id}_")]
                args[command_attribute] = matrix

        # Creates and applies constraint
        command = CreateBindingConstraint(**args)
        execute_or_add_commands(study, file_study, [command], self.storage_service)

        # Returns the new constraint
        source_constraint.name = new_constraint_name
        source_constraint.id = new_constraint_id
        return source_constraint

    def update_binding_constraint(
        self,
        study: Study,
        binding_constraint_id: str,
        data: ConstraintInput,
        existing_constraint: t.Optional[ConstraintOutput] = None,
    ) -> ConstraintOutput:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        existing_constraint = existing_constraint or self.get_binding_constraint(study, binding_constraint_id)

        study_version = StudyVersion.parse(study.version)
        check_attributes_coherence(data, study_version, data.operator or existing_constraint.operator)

        upd_constraint = {
            "id": binding_constraint_id,
            **data.model_dump(mode="json", exclude={"terms", "name"}, exclude_none=True),
        }
        args = {
            **upd_constraint,
            "command_context": self.storage_service.variant_study_service.command_factory.command_context,
            "study_version": study_version,
        }
        if data.terms:
            args["coeffs"] = self.terms_to_coeffs(data.terms)

        if data.time_step is not None and data.time_step != existing_constraint.time_step:
            # The user changed the time step, we need to update the matrix accordingly
            args = _replace_matrices_according_to_frequency_and_version(data, study_version, args)

        command = UpdateBindingConstraint(**args)

        # Validates the matrices. Needed when the study is a variant because we only append the command to the list
        if isinstance(study, VariantStudy):
            updated_matrices = [term for term in [m.value for m in TermMatrices] if getattr(data, term)]
            if updated_matrices:
                time_step = data.time_step or existing_constraint.time_step
                command.validates_and_fills_matrices(
                    time_step=time_step, specific_matrices=updated_matrices, version=study_version, create=False  # type: ignore
                )

        execute_or_add_commands(study, file_study, [command], self.storage_service)

        # Constructs the endpoint response.
        upd_constraint["name"] = existing_constraint.name
        upd_constraint["type"] = upd_constraint.get("time_step", existing_constraint.time_step)
        upd_constraint["terms"] = data.terms or existing_constraint.terms
        new_fields = ["enabled", "operator", "comments", "terms"]
        if study_version >= STUDY_VERSION_8_3:
            new_fields.extend(["filter_year_by_year", "filter_synthesis"])
        if study_version >= STUDY_VERSION_8_7:
            new_fields.append("group")
        for field in new_fields:
            if field not in upd_constraint:
                upd_constraint[field] = getattr(data, field) or getattr(existing_constraint, field)
        return self.constraint_model_adapter(upd_constraint, study_version)

    def update_binding_constraints(
        self,
        study: Study,
        bcs_by_ids: t.Mapping[str, ConstraintInput],
    ) -> t.Mapping[str, ConstraintOutput]:
        """
        Updates multiple binding constraints within a study.

        Args:
            study: The study from which to update the constraints.
            bcs_by_ids: A mapping of binding constraint IDs to their updated configurations.

        If there's more than 50 BCs updated as the same time, the 'update_binding_constraint' command takes more than 1 second.
        And for thousands of BCs updated as the same time, it takes several minutes.
        This is mainly because we open/close the 'bindingconstraints.ini' file multiple times for each constraint.
        To avoid this, when dealing with such a case we'll use the 'update_config' command to write all the data at once.
        However, such command is not really clear, so we won't use it on variants with less than 50 updated BCs.

        Returns:
            A dictionary of the updated binding constraints, indexed by their IDs.

        Raises:
            BindingConstraintNotFound: If any of the specified binding constraint IDs are not found.
        """

        # Variant study with less than 50 updated constraints
        updated_constraints = {}
        if len(bcs_by_ids) < 50 and isinstance(study, VariantStudy):
            existing_constraints = {bc.id: bc for bc in self.get_binding_constraints(study)}
            for bc_id, data in bcs_by_ids.items():
                updated_constraints[bc_id] = self.update_binding_constraint(
                    study, bc_id, data, existing_constraints[bc_id]
                )
            return updated_constraints

        # More efficient way of doing things but using less readable commands.
        study_version = StudyVersion.parse(study.version)
        commands = []
        command_context = self.storage_service.variant_study_service.command_factory.command_context

        file_study = self.storage_service.get_storage(study).get_raw(study)
        config = file_study.tree.get(["input", "bindingconstraints", "bindingconstraints"])
        dict_config = {value["id"]: key for (key, value) in config.items()}
        for bc_id, value in bcs_by_ids.items():
            if bc_id not in dict_config:
                raise BindingConstraintNotFound(f"Binding constraint '{bc_id}' not found")

            props = create_binding_constraint_config(study_version, **value.dict())
            new_values = props.model_dump(mode="json", by_alias=True, exclude_unset=True)
            upd_obj = config[dict_config[bc_id]]
            current_value = copy.deepcopy(upd_obj)
            upd_obj.update(new_values)
            output = self.constraint_model_adapter(upd_obj, study_version)
            updated_constraints[bc_id] = output

            if value.time_step and value.time_step != BindingConstraintFrequency(current_value["type"]):
                # The user changed the time step, we need to update the matrix accordingly
                replace_matrix_commands = _generate_replace_matrix_commands(
                    bc_id, study_version, value, output.operator, command_context
                )
                commands.extend(replace_matrix_commands)

            if value.operator and study_version >= STUDY_VERSION_8_7:
                # The user changed the operator, we have to rename matrices accordingly
                existing_operator = BindingConstraintOperator(current_value["operator"])
                update_matrices_names(file_study, bc_id, existing_operator, value.operator)

        # Updates the file only once with all the information
        command = UpdateConfig(
            target="input/bindingconstraints/bindingconstraints",
            data=config,
            command_context=command_context,
            study_version=study_version,
        )
        commands.append(command)
        execute_or_add_commands(study, file_study, commands, self.storage_service)
        return updated_constraints

    def remove_binding_constraint(self, study: Study, binding_constraint_id: str) -> None:
        """
        Removes a binding constraint from a study.

        Args:
            study: The study from which to remove the constraint.
            binding_constraint_id: The ID of the binding constraint to remove.

        Raises:
            BindingConstraintNotFound: If no binding constraint with the specified ID is found.
        """
        # Check the existence of the binding constraint before removing it
        bc = self.get_binding_constraint(study, binding_constraint_id)
        command_context = self.storage_service.variant_study_service.command_factory.command_context
        file_study = self.storage_service.get_storage(study).get_raw(study)
        command = RemoveBindingConstraint(
            id=bc.id, command_context=command_context, study_version=file_study.config.version
        )
        execute_or_add_commands(study, file_study, [command], self.storage_service)

    def remove_multiple_binding_constraints(self, study: Study, binding_constraints_ids: t.List[str]) -> None:
        """
        Removes multiple binding constraints from a study.

        Args:
            study: The study from which to remove the constraint.
            binding_constraints_ids: The IDs of the binding constraints to remove.

        Raises:
            BindingConstraintNotFound: If at least one binding constraint within the specified list is not found.
        """

        self.check_binding_constraints_exists(study, binding_constraints_ids)

        command_context = self.storage_service.variant_study_service.command_factory.command_context
        file_study = self.storage_service.get_storage(study).get_raw(study)

        command = RemoveMultipleBindingConstraints(
            ids=binding_constraints_ids,
            command_context=command_context,
            study_version=file_study.config.version,
        )

        execute_or_add_commands(study, file_study, [command], self.storage_service)

    def _update_constraint_with_terms(
        self, study: Study, bc: ConstraintOutput, terms: t.Mapping[str, ConstraintTerm]
    ) -> None:
        coeffs = {
            term_id: [term.weight, term.offset] if term.offset else [term.weight] for term_id, term in terms.items()
        }
        command_context = self.storage_service.variant_study_service.command_factory.command_context
        file_study = self.storage_service.get_storage(study).get_raw(study)
        args = {
            "id": bc.id,
            "coeffs": coeffs,
            "command_context": command_context,
            "study_version": file_study.config.version,
        }
        command = UpdateBindingConstraint.model_validate(args)
        execute_or_add_commands(study, file_study, [command], self.storage_service)

    def update_constraint_terms(
        self,
        study: Study,
        binding_constraint_id: str,
        constraint_terms: t.Sequence[ConstraintTerm],
        update_mode: str = "replace",
    ) -> None:
        """
        Update or add the specified constraint terms.

        Args:
            study: The study from which to update the binding constraint.
            binding_constraint_id: The ID of the binding constraint to update.
            constraint_terms: The constraint terms to update.
            update_mode: The update mode, either "replace" or "add".
        """
        if update_mode == "add":
            for term in constraint_terms:
                if term.data is None:
                    raise InvalidConstraintTerm(binding_constraint_id, term.model_dump_json())

        constraint = self.get_binding_constraint(study, binding_constraint_id)
        existing_terms = collections.OrderedDict((term.generate_id(), term) for term in constraint.terms)
        updated_terms = collections.OrderedDict((term.generate_id(), term) for term in constraint_terms)

        if update_mode == "replace":
            missing_terms = set(updated_terms) - set(existing_terms)
            if missing_terms:
                raise ConstraintTermNotFound(binding_constraint_id, *missing_terms)
        elif update_mode == "add":
            duplicate_terms = set(updated_terms) & set(existing_terms)
            if duplicate_terms:
                raise DuplicateConstraintTerm(binding_constraint_id, *duplicate_terms)
        else:  # pragma: no cover
            raise NotImplementedError(f"Unsupported update mode: {update_mode}")

        existing_terms.update(updated_terms)
        self._update_constraint_with_terms(study, constraint, existing_terms)

    def create_constraint_terms(
        self, study: Study, binding_constraint_id: str, constraint_terms: t.Sequence[ConstraintTerm]
    ) -> None:
        """
        Adds new constraint terms to an existing binding constraint.

        Args:
            study: The study from which to update the binding constraint.
            binding_constraint_id: The ID of the binding constraint to update.
            constraint_terms: The constraint terms to add.
        """
        return self.update_constraint_terms(study, binding_constraint_id, constraint_terms, update_mode="add")

    def remove_constraint_term(
        self,
        study: Study,
        binding_constraint_id: str,
        term_id: str,
    ) -> None:
        """
        Remove a constraint term from an existing binding constraint.

        Args:
            study: The study from which to update the binding constraint.
            binding_constraint_id: The ID of the binding constraint to update.
            term_id: The ID of the term to remove.
        """
        constraint = self.get_binding_constraint(study, binding_constraint_id)
        existing_terms = collections.OrderedDict((term.generate_id(), term) for term in constraint.terms)
        removed_term = existing_terms.pop(term_id, None)
        if removed_term is None:
            raise ConstraintTermNotFound(binding_constraint_id, term_id)
        self._update_constraint_with_terms(study, constraint, existing_terms)

    @staticmethod
    def get_table_schema() -> JSON:
        return ConstraintOutput870.schema()


def _replace_matrices_according_to_frequency_and_version(
    data: ConstraintInput, version: StudyVersion, args: t.Dict[str, t.Any]
) -> t.Dict[str, t.Any]:
    if version < STUDY_VERSION_8_7:
        if "values" not in args:
            matrix = {
                BindingConstraintFrequency.HOURLY.value: default_bc_hourly_86,
                BindingConstraintFrequency.DAILY.value: default_bc_weekly_daily_86,
                BindingConstraintFrequency.WEEKLY.value: default_bc_weekly_daily_86,
            }[data.time_step].tolist()
            args["values"] = matrix
    else:
        matrix = {
            BindingConstraintFrequency.HOURLY.value: default_bc_hourly_87,
            BindingConstraintFrequency.DAILY.value: default_bc_weekly_daily_87,
            BindingConstraintFrequency.WEEKLY.value: default_bc_weekly_daily_87,
        }[data.time_step].tolist()
        for term in [m.value for m in TermMatrices]:
            if term not in args:
                args[term] = matrix
    return args


def check_attributes_coherence(
    data: t.Union[ConstraintCreation, ConstraintInput],
    study_version: StudyVersion,
    operator: BindingConstraintOperator,
) -> None:
    if study_version < STUDY_VERSION_8_7:
        if data.group:
            raise InvalidFieldForVersionError(
                f"You cannot specify a group as your study version is older than v8.7: {data.group}"
            )
        if any([data.less_term_matrix, data.equal_term_matrix, data.greater_term_matrix]):
            raise InvalidFieldForVersionError("You cannot fill a 'matrix_term' as these values refer to v8.7+ studies")
    elif data.values:
        raise InvalidFieldForVersionError("You cannot fill 'values' as it refers to the matrix before v8.7")
    conflicting_matrices = [
        getattr(data, matrix) for matrix in OPERATOR_CONFLICT_MAP[operator] if getattr(data, matrix)
    ]
    if conflicting_matrices:
        raise InvalidFieldForVersionError(
            f"You cannot fill matrices '{OPERATOR_CONFLICT_MAP[operator]}' while using the operator '{operator}'"
        )
