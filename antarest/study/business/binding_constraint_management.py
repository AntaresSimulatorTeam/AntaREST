import collections
import itertools
import logging
from typing import Any, Dict, List, Mapping, MutableSequence, Optional, Sequence, Union

import numpy as np
from pydantic import BaseModel, Field, root_validator, validator
from requests.utils import CaseInsensitiveDict

from antarest.core.exceptions import (
    BindingConstraintNotFoundError,
    CommandApplicationError,
    ConstraintAlreadyExistError,
    ConstraintIdNotFoundError,
    DuplicateConstraintName,
    IncoherenceBetweenMatricesLength,
    InvalidConstraintName,
    InvalidFieldForVersionError,
    MissingDataError,
    NoConstraintError,
)
from antarest.core.utils.string import to_camel_case
from antarest.study.business.utils import AllOptionalMetaclass, camel_case_model, execute_or_add_commands
from antarest.study.model import Study
from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import BindingConstraintFrequency
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
from antarest.study.storage.variantstudy.model.command.common import BindingConstraintOperator
from antarest.study.storage.variantstudy.model.command.create_binding_constraint import (
    BindingConstraintMatrices,
    BindingConstraintProperties,
    BindingConstraintProperties870,
    CreateBindingConstraint,
)
from antarest.study.storage.variantstudy.model.command.remove_binding_constraint import RemoveBindingConstraint
from antarest.study.storage.variantstudy.model.command.update_binding_constraint import UpdateBindingConstraint
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy

logger = logging.getLogger(__name__)

DEFAULT_GROUP = "default"
"""Default group name for binding constraints if missing or empty."""


class LinkTerm(BaseModel):
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


class ClusterTerm(BaseModel):
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


class ConstraintTerm(BaseModel):
    """
    DTO for a constraint term.

    Attributes:
        id: the constraint term ID, of the form "area1%area2" or "area.cluster".
        weight: the constraint term weight, if any.
        offset: the constraint term offset, if any.
        data: the constraint term data (link or cluster), if any.
    """

    id: Optional[str]
    weight: Optional[float]
    offset: Optional[float]
    data: Optional[Union[LinkTerm, ClusterTerm]]

    @validator("id")
    def id_to_lower(cls, v: Optional[str]) -> Optional[str]:
        """Ensure the ID is lower case."""
        if v is None:
            return None
        return v.lower()

    def generate_id(self) -> str:
        """Return the constraint term ID for this term based on its data."""
        if self.data is None:
            return self.id or ""
        return self.data.generate_id()


class ConstraintFilters(BaseModel, frozen=True, extra="forbid"):
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
    enabled: Optional[bool] = None
    operator: Optional[BindingConstraintOperator] = None
    comments: str = ""
    group: str = ""
    time_step: Optional[BindingConstraintFrequency] = None
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
            return False
        if self.enabled is not None and self.enabled != constraint.enabled:
            return False
        if self.operator is not None and self.operator != constraint.operator:
            return False
        if self.comments:
            comments = constraint.comments or ""
            if self.comments.upper() not in comments.upper():
                return False
        if self.group:
            group = getattr(constraint, "group", DEFAULT_GROUP)
            if self.group.upper() != group.upper():
                return False
        if self.time_step is not None and self.time_step != constraint.time_step:
            return False

        # Filter on terms
        terms = constraint.terms or []

        if self.area_name:
            matching_terms = []

            for term in terms:
                if term.data:
                    if isinstance(term.data, LinkTerm):
                        # Check if either area in the link matches the specified area_name
                        if self.area_name.upper() in (term.data.area1.upper(), term.data.area2.upper()):
                            matching_terms.append(term)
                    elif isinstance(term.data, ClusterTerm):
                        # Check if the cluster's area matches the specified area_name
                        if self.area_name.upper() == term.data.area.upper():
                            matching_terms.append(term)

            # If no terms match, the constraint should not pass
            if not matching_terms:
                return False

        if self.cluster_name:
            all_clusters = []
            for term in terms:
                if term.data is None:
                    continue
                if isinstance(term.data, ClusterTerm):
                    all_clusters.append(term.data.cluster)
            upper_cluster_name = self.cluster_name.upper()
            if all_clusters and not any(upper_cluster_name in cluster.upper() for cluster in all_clusters):
                return False

        if self.link_id:
            all_link_ids = [term.data.generate_id() for term in terms if isinstance(term.data, LinkTerm)]
            if not any(self.link_id.lower() == link_id.lower() for link_id in all_link_ids):
                return False

        if self.cluster_id:
            all_cluster_ids = [term.data.generate_id() for term in terms if isinstance(term.data, ClusterTerm)]
            if not any(self.cluster_id.lower() == cluster_id.lower() for cluster_id in all_cluster_ids):
                return False

        return True


@camel_case_model
class ConstraintInput870(BindingConstraintProperties870, metaclass=AllOptionalMetaclass, use_none=True):
    pass


@camel_case_model
class ConstraintInput(BindingConstraintMatrices, ConstraintInput870):
    terms: MutableSequence[ConstraintTerm] = Field(
        default_factory=lambda: [],
    )


@camel_case_model
class ConstraintCreation(ConstraintInput):
    name: str

    @root_validator(pre=True)
    def check_matrices_dimensions(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        for _key in ["time_step", "less_term_matrix", "equal_term_matrix", "greater_term_matrix"]:
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
        expected_rows = {
            BindingConstraintFrequency.HOURLY: 8784,
            BindingConstraintFrequency.DAILY: 366,
            BindingConstraintFrequency.WEEKLY: 366,
        }[_time_step]

        # Collect the matrix shapes
        matrix_shapes = {}
        for _field_name in ["values", "less_term_matrix", "equal_term_matrix", "greater_term_matrix"]:
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


@camel_case_model
class ConstraintOutputBase(BindingConstraintProperties):
    id: str
    name: str
    terms: MutableSequence[ConstraintTerm] = Field(
        default_factory=lambda: [],
    )


@camel_case_model
class ConstraintOutput870(ConstraintOutputBase):
    group: str


ConstraintOutput = Union[ConstraintOutputBase, ConstraintOutput870]


def _validate_binding_constraints(file_study: FileStudy, bcs: Sequence[ConstraintOutput]) -> bool:
    if int(file_study.config.version) < 870:
        matrix_id_fmts = {"{bc_id}"}
    else:
        matrix_id_fmts = {"{bc_id}_eq", "{bc_id}_lt", "{bc_id}_gt"}

    references_by_shapes = collections.defaultdict(list)
    _total = len(bcs) * len(matrix_id_fmts)
    for _index, (bc, fmt) in enumerate(itertools.product(bcs, matrix_id_fmts), 1):
        matrix_id = fmt.format(bc_id=bc.id)
        logger.info(f"⏲ Validating BC '{bc.id}': {matrix_id=} [{_index}/{_total}]")
        _obj = file_study.tree.get(url=["input", "bindingconstraints", matrix_id])
        _array = np.array(_obj["data"], dtype=float)
        if _array.size == 0 or _array.shape[1] == 1:
            continue
        references_by_shapes[_array.shape].append((bc.id, matrix_id))
        del _obj
        del _array

    if len(references_by_shapes) > 1:
        most_common = collections.Counter(references_by_shapes.keys()).most_common()
        invalid_constraints = collections.defaultdict(list)
        for shape, _ in most_common[1:]:
            references = references_by_shapes[shape]
            for bc_id, matrix_id in references:
                invalid_constraints[bc_id].append(f"'{matrix_id}' {shape}")
        expected_shape = most_common[0][0]
        detail = {
            "msg": f"Matrix shapes mismatch in binding constraints group. Expected shape: {expected_shape}",
            "invalid_constraints": dict(invalid_constraints),
        }
        raise IncoherenceBetweenMatricesLength(detail)

    return True


class BindingConstraintManager:
    def __init__(
        self,
        storage_service: StudyStorageService,
    ) -> None:
        self.storage_service = storage_service

    @staticmethod
    def parse_constraint(key: str, value: str, char: str, new_config: ConstraintOutput) -> bool:
        split = key.split(char)
        if len(split) == 2:
            value1 = split[0]
            value2 = split[1]
            weight = 0.0
            offset = None
            try:
                weight = float(value)
            except ValueError:
                weight_and_offset = value.split("%")
                if len(weight_and_offset) == 2:
                    weight = float(weight_and_offset[0])
                    offset = float(weight_and_offset[1])
            if new_config.terms is None:
                new_config.terms = []
            new_config.terms.append(
                ConstraintTerm(
                    id=key,
                    weight=weight,
                    offset=offset if offset is not None else None,
                    data=LinkTerm(
                        area1=value1,
                        area2=value2,
                    )
                    if char == "%"
                    else ClusterTerm(
                        area=value1,
                        cluster=value2,
                    ),
                )
            )
            return True
        return False

    @staticmethod
    def constraint_model_adapter(constraint: Mapping[str, Any], version: int) -> ConstraintOutput:
        """
        Adapts a constraint configuration to the appropriate version-specific format.

        Parameters:
        - constraint: A dictionary or model representing the constraint to be adapted.
                    This can either be a dictionary coming from client input or an existing
                    model that needs reformatting.
        - version: An integer indicating the target version of the study configuration. This is used to
                determine which model class to instantiate and which default values to apply.

        Returns:
        - A new instance of either `ConstraintOutputBase` or `ConstraintOutput870`,
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
            "time_step": constraint.get("type", BindingConstraintFrequency.HOURLY),
            "operator": constraint.get("operator", BindingConstraintOperator.EQUAL),
            "comments": constraint.get("comments", ""),
            "filter_year_by_year": constraint.get("filter_year_by_year", ""),
            "filter_synthesis": constraint.get("filter_synthesis", ""),
            "terms": constraint.get("terms", []),
        }

        if version < 870:
            adapted_constraint = ConstraintOutputBase(**constraint_output)
        else:
            constraint_output["group"] = constraint.get("group", DEFAULT_GROUP)
            adapted_constraint = ConstraintOutput870(**constraint_output)

        for key, value in constraint.items():
            if BindingConstraintManager.parse_constraint(key, value, "%", adapted_constraint):
                continue
            if BindingConstraintManager.parse_constraint(key, value, ".", adapted_constraint):
                continue
        return adapted_constraint

    @staticmethod
    def terms_to_coeffs(terms: Sequence[ConstraintTerm]) -> Dict[str, List[float]]:
        """
        Converts a sequence of terms into a dictionary mapping each term's ID to its coefficients,
        including the weight and, optionally, the offset.

        :param terms: A sequence of terms to be converted.
        :return: A dictionary of term IDs mapped to a list of their coefficients.
        """
        coeffs = {}

        if terms is not None:
            for term in terms:
                if term.id and term.weight is not None:
                    coeffs[term.id] = [term.weight]
                    if term.offset is not None:
                        coeffs[term.id].append(term.offset)

            return coeffs

    def get_binding_constraint(
        self,
        study: Study,
        filters: ConstraintFilters = ConstraintFilters(),
    ) -> Union[ConstraintOutput, List[ConstraintOutput]]:
        storage_service = self.storage_service.get_storage(study)
        file_study = storage_service.get_raw(study)
        config = file_study.tree.get(["input", "bindingconstraints", "bindingconstraints"])

        # TODO: if a single constraint ID is passed, and don't exist in the config raise an execption

        constraints_by_id: Dict[str, ConstraintOutput] = {}

        for constraint in config.values():
            constraint_config = self.constraint_model_adapter(constraint, int(study.version))
            constraints_by_id[constraint_config.id] = constraint_config

        filtered_constraints = {bc_id: bc for bc_id, bc in constraints_by_id.items() if filters.match_filters(bc)}

        # If a specific constraint ID is provided, we return that constraint
        if filters.bc_id:
            return filtered_constraints.get(filters.bc_id) # type: ignore

        # Else we return all the matching constraints, based on the given filters
        return list(filtered_constraints.values())  

    def get_grouped_constraints(self, study: Study) -> Mapping[str, Sequence[ConstraintOutput]]:
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
        grouped_constraints = CaseInsensitiveDict()  # type: ignore

        for constraint in config.values():
            constraint_config = self.constraint_model_adapter(constraint, int(study.version))
            constraint_group = getattr(constraint_config, "group", DEFAULT_GROUP)
            grouped_constraints.setdefault(constraint_group, []).append(constraint_config)

        return grouped_constraints

    def get_constraints_by_group(self, study: Study, group_name: str) -> Sequence[ConstraintOutput]:
        """
         Retrieve all binding constraints belonging to a specified group within a study.

        Args:
            study: The study from which to retrieve the constraints.
            group_name: The name of the group (case-insensitive).

        Returns:
            A list of ConstraintOutput objects that belong to the specified group.

        Raises:
            BindingConstraintNotFoundError: If the specified group name is not found among the constraint groups.
        """
        grouped_constraints = self.get_grouped_constraints(study)

        if group_name not in grouped_constraints:
            raise BindingConstraintNotFoundError(f"Group '{group_name}' not found")

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
            BindingConstraintNotFoundError: If no matching group name is found in a case-insensitive manner.
        """
        storage_service = self.storage_service.get_storage(study)
        file_study = storage_service.get_raw(study)
        grouped_constraints = self.get_grouped_constraints(study)

        if group_name not in grouped_constraints:
            raise BindingConstraintNotFoundError(f"Group '{group_name}' not found")

        constraints = grouped_constraints[group_name]
        return _validate_binding_constraints(file_study, constraints)

    def validate_constraint_groups(self, study: Study) -> bool:
        """
        Validates all groups of binding constraints within the given study.

        This method checks each group of binding constraints for validity based on specific criteria
        (e.g., coherence between matrices lengths). If any group fails the validation, an aggregated
        error detailing all incoherences is raised.

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
            except IncoherenceBetweenMatricesLength as e:
                invalid_groups[group_name] = e.detail

        if invalid_groups:
            raise IncoherenceBetweenMatricesLength(invalid_groups)

        return True

    def create_binding_constraint(
        self,
        study: Study,
        data: ConstraintCreation,
    ) -> ConstraintOutput:
        bc_id = transform_name_to_id(data.name)
        version = int(study.version)

        if not bc_id:
            raise InvalidConstraintName(f"Invalid binding constraint name: {data.name}.")

        if bc_id in {bc.id for bc in self.get_binding_constraint(study)}:  # type: ignore
            raise DuplicateConstraintName(f"A binding constraint with the same name already exists: {bc_id}.")

        check_attributes_coherence(data, version)

        new_constraint = {
            "name": data.name,
            "enabled": data.enabled,
            "time_step": data.time_step,
            "operator": data.operator,
            "coeffs": self.terms_to_coeffs(data.terms),
            "values": data.values,
            "less_term_matrix": data.less_term_matrix,
            "equal_term_matrix": data.equal_term_matrix,
            "greater_term_matrix": data.greater_term_matrix,
            "filter_year_by_year": data.filter_year_by_year,
            "filter_synthesis": data.filter_synthesis,
            "comments": data.comments or "",
        }

        if version >= 870:
            new_constraint["group"] = data.group or DEFAULT_GROUP

        command = CreateBindingConstraint(
            **new_constraint, command_context=self.storage_service.variant_study_service.command_factory.command_context
        )

        # Validates the matrices. Needed when the study is a variant because we only append the command to the list
        if isinstance(study, VariantStudy):
            command.validates_and_fills_matrices(specific_matrices=None, version=version, create=True)

        file_study = self.storage_service.get_storage(study).get_raw(study)
        execute_or_add_commands(study, file_study, [command], self.storage_service)

        # Processes the constraints to add them inside the endpoint response.
        new_constraint["id"] = bc_id
        new_constraint["type"] = data.time_step
        return self.constraint_model_adapter(new_constraint, version)

    def update_binding_constraint(
        self,
        study: Study,
        binding_constraint_id: str,
        data: ConstraintInput,
    ) -> ConstraintOutput:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        existing_constraint = self.get_binding_constraint(study, ConstraintFilters(bc_id=binding_constraint_id))
        study_version = int(study.version)
        if not isinstance(existing_constraint, ConstraintOutputBase) and not isinstance(
            existing_constraint, ConstraintOutput870
        ):
            raise BindingConstraintNotFoundError(study.id)

        check_attributes_coherence(data, study_version)

        # Because the update_binding_constraint command requires every attribute we have to fill them all.
        # This creates a `big` command even though we only updated one field.
        # fixme : Change the architecture to avoid this type of misconception
        updated_constraint = {
            "id": binding_constraint_id,
            "enabled": data.enabled if data.enabled is not None else existing_constraint.enabled,
            "time_step": data.time_step or existing_constraint.time_step,
            "operator": data.operator or existing_constraint.operator,
            "coeffs": self.terms_to_coeffs(data.terms) or self.terms_to_coeffs(existing_constraint.terms),
            "filter_year_by_year": data.filter_year_by_year or existing_constraint.filter_year_by_year,
            "filter_synthesis": data.filter_synthesis or existing_constraint.filter_synthesis,
            "comments": data.comments or existing_constraint.comments,
        }

        if study_version >= 870:
            updated_constraint["group"] = data.group or existing_constraint.group  # type: ignore

        args = {
            **updated_constraint,
            "command_context": self.storage_service.variant_study_service.command_factory.command_context,
        }

        for term in ["values", "less_term_matrix", "equal_term_matrix", "greater_term_matrix"]:
            if matrices_to_update := getattr(data, term):
                args[term] = matrices_to_update

        if data.time_step is not None and data.time_step != existing_constraint.time_step:
            # The user changed the time step, we need to update the matrix accordingly
            args = _replace_matrices_according_to_frequency_and_version(data, study_version, args)

        command = UpdateBindingConstraint(**args)

        # Validates the matrices. Needed when the study is a variant because we only append the command to the list
        if isinstance(study, VariantStudy):
            updated_matrices = [
                term for term in ["less_term_matrix", "equal_term_matrix", "greater_term_matrix"] if getattr(data, term)
            ]
            command.validates_and_fills_matrices(
                specific_matrices=updated_matrices, version=study_version, create=False
            )

        execute_or_add_commands(study, file_study, [command], self.storage_service)

        # Processes the constraints to add them inside the endpoint response.
        updated_constraint["name"] = existing_constraint.name
        updated_constraint["type"] = updated_constraint["time_step"]
        # Replace coeffs by the terms
        del updated_constraint["coeffs"]
        updated_constraint["terms"] = data.terms or existing_constraint.terms

        return self.constraint_model_adapter(updated_constraint, study_version)

    def remove_binding_constraint(self, study: Study, binding_constraint_id: str) -> None:
        command = RemoveBindingConstraint(
            id=binding_constraint_id,
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )
        file_study = self.storage_service.get_storage(study).get_raw(study)

        # Needed when the study is a variant because we only append the command to the list
        if isinstance(study, VariantStudy) and not self.get_binding_constraint(
            study, ConstraintFilters(bc_id=binding_constraint_id)
        ):
            raise CommandApplicationError("Binding constraint not found")

        execute_or_add_commands(study, file_study, [command], self.storage_service)

    def update_constraint_term(
        self,
        study: Study,
        binding_constraint_id: str,
        term: ConstraintTerm,
    ) -> None:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        constraint = self.get_binding_constraint(study, ConstraintFilters(bc_id=binding_constraint_id))

        if not isinstance(constraint, ConstraintOutputBase) and not isinstance(constraint, ConstraintOutputBase):
            raise BindingConstraintNotFoundError(study.id)

        constraint_terms = constraint.terms  # existing constraint terms
        if constraint_terms is None:
            raise NoConstraintError(study.id)

        term_id = term.id if isinstance(term, ConstraintTerm) else term
        if term_id is None:
            raise ConstraintIdNotFoundError(study.id)

        term_id_index = find_constraint_term_id(constraint_terms, term_id)
        if term_id_index < 0:
            raise ConstraintIdNotFoundError(study.id)

        if isinstance(term, ConstraintTerm):
            updated_term_id = term.data.generate_id() if term.data else term_id
            current_constraint = constraint_terms[term_id_index]

            constraint_terms[term_id_index] = ConstraintTerm(
                id=updated_term_id,
                weight=term.weight or current_constraint.weight,
                offset=term.offset,
                data=term.data or current_constraint.data,
            )
        else:
            del constraint_terms[term_id_index]

        coeffs = {term.id: [term.weight, term.offset] if term.offset else [term.weight] for term in constraint_terms}

        command = UpdateBindingConstraint(
            id=constraint.id,
            enabled=constraint.enabled,
            time_step=constraint.time_step,
            operator=constraint.operator,
            coeffs=coeffs,
            filter_year_by_year=constraint.filter_year_by_year,
            filter_synthesis=constraint.filter_synthesis,
            comments=constraint.comments,
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )
        execute_or_add_commands(study, file_study, [command], self.storage_service)

    def create_constraint_term(
        self,
        study: Study,
        binding_constraint_id: str,
        constraint_term: ConstraintTerm,
    ) -> None:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        constraint = self.get_binding_constraint(study, ConstraintFilters(bc_id=binding_constraint_id))
        if not isinstance(constraint, ConstraintOutputBase) and not isinstance(constraint, ConstraintOutputBase):
            raise BindingConstraintNotFoundError(study.id)

        if constraint_term.data is None:
            raise MissingDataError("Add new constraint term : data is missing")

        constraint_id = constraint_term.data.generate_id()
        constraint_terms = constraint.terms or []
        if find_constraint_term_id(constraint_terms, constraint_id) >= 0:
            raise ConstraintAlreadyExistError(study.id)

        constraint_terms.append(
            ConstraintTerm(
                id=constraint_id,
                weight=constraint_term.weight if constraint_term.weight is not None else 0.0,
                offset=constraint_term.offset,
                data=constraint_term.data,
            )
        )

        coeffs = {}

        for term in constraint_terms:
            coeffs[term.id] = [term.weight]
            if term.offset is not None:
                coeffs[term.id].append(term.offset)

        command = UpdateBindingConstraint(
            id=constraint.id,
            enabled=constraint.enabled,
            time_step=constraint.time_step,
            operator=constraint.operator,
            coeffs=coeffs,
            comments=constraint.comments,
            filter_year_by_year=constraint.filter_year_by_year,
            filter_synthesis=constraint.filter_synthesis,
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )
        execute_or_add_commands(study, file_study, [command], self.storage_service)

    # FIXME create a dedicated delete service
    def remove_constraint_term(
        self,
        study: Study,
        binding_constraint_id: str,
        term_id: str,
    ) -> None:
        return self.update_constraint_term(study, binding_constraint_id, term_id)  # type: ignore


def _replace_matrices_according_to_frequency_and_version(
    data: ConstraintInput, version: int, args: Dict[str, Any]
) -> Dict[str, Any]:
    if version < 870:
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
        for term in ["less_term_matrix", "equal_term_matrix", "greater_term_matrix"]:
            if term not in args:
                args[term] = matrix
    return args


def find_constraint_term_id(constraints_term: Sequence[ConstraintTerm], constraint_term_id: str) -> int:
    try:
        index = [elm.id for elm in constraints_term].index(constraint_term_id)
        return index
    except ValueError:
        return -1


def check_attributes_coherence(data: Union[ConstraintCreation, ConstraintInput], study_version: int) -> None:
    if study_version < 870:
        if data.group:
            raise InvalidFieldForVersionError(
                f"You cannot specify a group as your study version is older than v8.7: {data.group}"
            )
        if any([data.less_term_matrix, data.equal_term_matrix, data.greater_term_matrix]):
            raise InvalidFieldForVersionError("You cannot fill a 'matrix_term' as these values refer to v8.7+ studies")
    elif data.values:
        raise InvalidFieldForVersionError("You cannot fill 'values' as it refers to the matrix before v8.7")
