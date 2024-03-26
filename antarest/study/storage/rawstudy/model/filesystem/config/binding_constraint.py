"""
Object model used to read and update binding constraint configuration.
"""
import json
import typing as t

from pydantic import Field, root_validator, validator

from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.storage.rawstudy.model.filesystem.config.field_validators import validate_filtering
from antarest.study.storage.rawstudy.model.filesystem.config.ini_properties import IniProperties


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


class AbstractTerm(IniProperties):
    """
    Abstract term of a binding constraint.

    Attributes:
        weight: weight of the term
        offset: offset of the term
    """

    weight: float = 0.0
    offset: int = 0

    def __str__(self) -> str:
        """String representation used in configuration files."""
        term_id = self.bc_id
        value = self.bc_value
        return f"{term_id} = {value}" if term_id else value

    @property
    def bc_id(self) -> str:
        """Return the constraint term ID for this constraint."""
        # Method should be overridden in child class.
        # It is implemented here to avoid raising an error in the debugger.
        return ""

    @property
    def bc_value(self) -> str:
        """Return the constraint term value for this constraint."""
        return f"{self.weight}%{self.offset}" if self.offset else str(self.weight)


class LinkTerm(AbstractTerm):
    """
    Term of a binding constraint applied to a link.

    Attributes:
        weight: weight of the term
        offset: offset of the term
        area1_id: ID of the first area
        area2_id: ID of the second area
    """

    area1_id: str = Field(alias="area1")
    area2_id: str = Field(alias="area2")

    @property
    def bc_id(self) -> str:
        """
        Return the constraint term ID for this constraint on a link,
        of the form "area1%area2".
        """
        # Ensure IDs are in alphabetical order and lower case
        ids = sorted((self.area1_id.lower(), self.area2_id.lower()))
        return "%".join(ids)


class ClusterTerm(AbstractTerm):
    """
    Term of a binding constraint applied to a thermal cluster.

    Attributes:
        weight: weight of the term
        offset: offset of the term
        area_id: ID of the area
        cluster_id: ID of the cluster
    """

    area_id: str = Field(alias="area")
    cluster_id: str = Field(alias="cluster")

    @property
    def bc_id(self) -> str:
        """
        Return the constraint term ID for this constraint on thermal cluster,
        of the form "area.cluster".
        """
        # Ensure IDs are in lower case
        ids = [self.area_id.lower(), self.cluster_id.lower()]
        return ".".join(ids)


BindingConstraintTerm = t.Union[LinkTerm, ClusterTerm]
"""
This type represents the list of possible term types for a binding constraint.
This union can be extended with new term types in the future.
"""


def build_term_from_config(term_id: str, value: t.Union[str, int, float]) -> BindingConstraintTerm:
    """
    Create a term from a string extracted from the configuration file.
    """
    # Extract the weight and offset from the value
    if isinstance(value, (int, float)):
        weight, offset = float(value), 0.0
    else:
        weight, offset = map(float, value.split("%")) if "%" in value else (float(value), 0.0)

    # Parse the term ID
    if "%" in term_id:
        # - Link: "{area1_id}%{area2_id} = {weight}"
        # - Link with offset: "{area1_id}%{area2_id} = {weight}%{offset}"
        area1_id, area2_id = term_id.split("%")
        return LinkTerm(weight=weight, offset=offset, area1_id=area1_id, area2_id=area2_id)

    elif "." in term_id:
        # - Cluster: "{area_id}.{cluster_id} = {weight}"
        # - Cluster with offset: "{area_id}.{cluster_id} = {weight}%{offset}"
        area_id, cluster_id = term_id.split(".")
        return ClusterTerm(weight=weight, offset=offset, area_id=area_id, cluster_id=cluster_id)

    else:
        raise ValueError(f"Invalid term ID: {term_id}")


def build_term_from_obj(obj: t.Mapping[str, t.Any]) -> BindingConstraintTerm:
    """
    Create a term from a dictionary extracted from another object.
    """
    for cls in BindingConstraintTerm.__args__:  # type: ignore
        try:
            return t.cast(BindingConstraintTerm, cls.parse_obj(obj))
        except ValueError:
            pass
    raise ValueError(f"Invalid term object: {obj!r}")


def _generate_bc_id(name: t.Optional[str]) -> t.Optional[str]:
    """
    Generate a binding constraint ID from the name.
    Return ``None`` if the name is not set or invalid.
    """
    # If the name is not set, return None
    if not name:
        return None

    # Lazy import to avoid circular import
    from antarest.study.storage.rawstudy.model.filesystem.config.model import transform_name_to_id

    bc_id = transform_name_to_id(name, lower=True)
    return bc_id or None  # Ensure None if empty string


# noinspection SpellCheckingInspection
class BindingConstraintProperties(IniProperties):
    """
    Configuration read from the `input/bindingconstraints/bindingconstraints.ini` file.

    This file contains a section for each binding constraint.
    Section names correspond to a 0-based index in the list of constraints.

    But, since each binding constraint has a unique ID, we use a mapping of IDs to sections.

    >>> from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import BindingConstraintProperties
    >>> from pprint import pprint

    Create and validate a new BindingConstraintProperties from a dictionary read from a configuration file.

    >>> obj = {
    ...     "0": {
    ...         "name": "DSR_AT_stock",
    ...         "id": "dsr_at_stock",
    ...         "enabled": True,
    ...         "type": "daily",
    ...         "operator": "less",
    ...         "at.at_dsr 0": 6.5,
    ...     },
    ...     "1": {
    ...         "name": "DSR_BE_stock",
    ...         "enabled": False,
    ...         "type": "daily",
    ...         "operator": "greater",
    ...         "be.be_dsr 0": 8.3,
    ...     },
    ... }

    >>> bc = BindingConstraintProperties.parse_obj(obj)
    >>> constraints = sorted(bc.constraints.values(), key=lambda s: s.id)
    >>> pprint([s.dict(by_alias=True) for s in constraints])
    [{'comments': '',
      'enabled': True,
      'filter-synthesis': 'hourly, daily, weekly, monthly, annual',
      'filter-year-by-year': 'hourly, daily, weekly, monthly, annual',
      'id': 'dsr_at_stock',
      'name': 'DSR_AT_stock',
      'operator': <BindingConstraintOperator.LESS: 'less'>,
      'terms': {'at.at_dsr 0': {'area': 'at',
                                'cluster': 'at_dsr 0',
                                'offset': 0,
                                'weight': 6.5}},
      'type': <BindingConstraintFrequency.DAILY: 'daily'>},
     {'comments': '',
      'enabled': False,
      'filter-synthesis': 'hourly, daily, weekly, monthly, annual',
      'filter-year-by-year': 'hourly, daily, weekly, monthly, annual',
      'id': 'dsr_be_stock',
      'name': 'DSR_BE_stock',
      'operator': <BindingConstraintOperator.GREATER: 'greater'>,
      'terms': {'be.be_dsr 0': {'area': 'be',
                                'cluster': 'be_dsr 0',
                                'offset': 0,
                                'weight': 8.3}},
      'type': <BindingConstraintFrequency.DAILY: 'daily'>}]
    """

    class BindingConstraintSection(IniProperties):
        """
        Configuration read from a section in the `input/bindingconstraints/bindingconstraints.ini` file.

        >>> from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import BindingConstraintProperties
        >>> from pprint import pprint

        Create and validate a new BindingConstraintSection from a dictionary read from a configuration file.

        >>> obj = {
        ...     "name": "FB001",
        ...     "id": "fb001",
        ...     "enabled": True,
        ...     "type": "hourly",
        ...     "operator": "less",
        ...     "filter-synthesis": "hourly, annual",
        ...     "filter-year-by-year": "",
        ...     "at.cl1": 1,
        ...     "de.cl2": "-88.77%7",
        ...     "at%de": -0.06,
        ...     "at%es": "8.5%5",
        ... }

        >>> bc = BindingConstraintProperties.BindingConstraintSection.parse_obj(obj)
        >>> pprint(bc.dict(by_alias=True))
        {'comments': '',
         'enabled': True,
         'filter-synthesis': 'hourly, annual',
         'filter-year-by-year': '',
         'id': 'fb001',
         'name': 'FB001',
         'operator': <BindingConstraintOperator.LESS: 'less'>,
         'terms': {'at%de': {'area1': 'at',
                             'area2': 'de',
                             'offset': 0,
                             'weight': -0.06},
                   'at%es': {'area1': 'at', 'area2': 'es', 'offset': 5, 'weight': 8.5},
                   'at.cl1': {'area': 'at',
                              'cluster': 'cl1',
                              'offset': 0,
                              'weight': 1.0},
                   'de.cl2': {'area': 'de',
                              'cluster': 'cl2',
                              'offset': 7,
                              'weight': -88.77}},
         'type': <BindingConstraintFrequency.HOURLY: 'hourly'>}

        We can construct a BindingConstraintSection from a dictionary.

        >>> bc2 = BindingConstraintProperties.BindingConstraintSection.parse_obj(bc.dict())
        >>> bc2 == bc
        True

        Convert the BindingConstraintSection to a dictionary for writing to a configuration file.

        >>> pprint(bc2.to_config())
        {'at%de': '-0.06',
         'at%es': '8.5%5',
         'at.cl1': '1.0',
         'comments': '',
         'de.cl2': '-88.77%7',
         'enabled': True,
         'filter-synthesis': 'hourly, annual',
         'filter-year-by-year': '',
         'id': 'fb001',
         'name': 'FB001',
         'operator': 'less',
         'type': 'hourly'}
        """

        id: str
        name: str
        enabled: bool = True
        time_step: BindingConstraintFrequency = Field(default=BindingConstraintFrequency.HOURLY, alias="type")
        operator: BindingConstraintOperator = BindingConstraintOperator.EQUAL
        comments: str = ""
        filter_synthesis: str = Field(default="hourly, daily, weekly, monthly, annual", alias="filter-synthesis")
        filter_year_by_year: str = Field(default="hourly, daily, weekly, monthly, annual", alias="filter-year-by-year")

        terms: t.MutableMapping[str, BindingConstraintTerm] = Field(default_factory=dict)

        @root_validator(pre=True)
        def _populate_section(cls, values: t.MutableMapping[str, t.Any]) -> t.MutableMapping[str, t.Any]:
            """
            Parse the section properties and terms from the configuration file.
            """

            # Extract known properties to leave only terms
            new_values = {
                "id": values.pop("id", None),
                "name": values.pop("name", None),
                "enabled": values.pop("enabled", None),
                "type": values.pop("time_step", None),
                "operator": values.pop("operator", None),
                "comments": values.pop("comments", None),
                "filter-synthesis": values.pop("filter_synthesis", None),
                "filter-year-by-year": values.pop("filter_year_by_year", None),
            }

            if new_values["id"] is None:
                new_values["id"] = _generate_bc_id(new_values["name"])
            if new_values["type"] is None:
                new_values["type"] = values.pop("type", None)
            if new_values["filter-synthesis"] is None:
                new_values["filter-synthesis"] = values.pop("filter-synthesis", None)
            if new_values["filter-year-by-year"] is None:
                new_values["filter-year-by-year"] = values.pop("filter-year-by-year", None)

            # Collect terms
            new_values["terms"] = terms = {}
            if "terms" in values:
                for value in values.pop("terms").values():
                    obj = value if isinstance(value, dict) else value.dict()
                    term = build_term_from_obj(obj)
                    terms[term.bc_id] = term
            else:
                for term_id, value in values.items():
                    term = build_term_from_config(term_id, value)
                    terms[term.bc_id] = term

            # Drop `None` values so that we can use the default values, but keep "" values
            new_values = {k: v for k, v in new_values.items() if v is not None}

            return new_values

        _validate_filtering = validator(
            "filter_synthesis",
            "filter_year_by_year",
            pre=True,
            allow_reuse=True,
        )(validate_filtering)

        def to_config(self) -> t.Mapping[str, t.Any]:
            config_values = {
                "id": self.id,
                "name": self.name,
                "enabled": self.enabled,
                "type": self.time_step,
                "operator": self.operator,
                "comments": self.comments,
                "filter-synthesis": self.filter_synthesis,
                "filter-year-by-year": self.filter_year_by_year,
            }

            for term_id, term in sorted(self.terms.items()):
                config_values[term_id] = term.bc_value

            # Convert to a dictionary for writing to a configuration file
            config_values = {k: json.loads(json.dumps(v)) for k, v in config_values.items()}

            return config_values

        def insert_term(self, term: BindingConstraintTerm) -> None:
            """
            Insert a new term into the section.
            """
            term_id = term.bc_id
            if term_id in self.terms:
                raise ValueError(f"Term '{term_id}' already exists in the binding constraint '{self.id}'.")
            self.terms[term_id] = term

        def remove_term(self, term_id: str) -> None:
            """
            Remove a term from the section.
            """
            if term_id not in self.terms:
                raise ValueError(f"Term '{term_id}' does not exist in the binding constraint '{self.id}'.")
            del self.terms[term_id]

        def update_term(self, term: BindingConstraintTerm) -> None:
            """
            Update an existing term in the section.
            """
            term_id = term.bc_id
            if term_id not in self.terms:
                raise ValueError(f"Term '{term_id}' does not exist in the binding constraint '{self.id}'.")
            self.terms[term_id] = term

        def get_term(self, term_id: str) -> BindingConstraintTerm:
            """
            Get a term from the section.
            """
            if term_id not in self.terms:
                raise ValueError(f"Term '{term_id}' does not exist in the binding constraint '{self.id}'.")
            return self.terms[term_id]

    constraints: t.MutableMapping[str, BindingConstraintSection] = Field(default_factory=dict)

    @root_validator(pre=True)
    def _populate_constraints(cls, values: t.MutableMapping[str, t.Any]) -> t.MutableMapping[str, t.Any]:
        """
        Parse the sections from the configuration file.
        """
        parse_obj = BindingConstraintProperties.BindingConstraintSection.parse_obj
        constraints = {}

        if "constraints" in values:
            # Case where the dictionary comes from another BindingConstraintProperties object
            for section_value in values["constraints"].values():
                obj = section_value if isinstance(section_value, dict) else section_value.dict()
                bc = parse_obj(obj)
                constraints[bc.id] = bc

        else:
            # Case where the dictionary comes from a configuration file
            for section_value in values.values():
                section = parse_obj(section_value)
                constraints[section.id] = section

        return {"constraints": constraints}

    def to_config(self) -> t.Mapping[str, t.Any]:
        # Constraints are sorted by ID to ensure consistent output for testing
        constraints = sorted(self.constraints.values(), key=lambda section: section.id)
        return {str(i): section.to_config() for i, section in enumerate(constraints)}

    def insert_constraint(self, constraint: BindingConstraintSection) -> None:
        """
        Insert a new constraint into the configuration.
        """
        if constraint.id in self.constraints:
            raise ValueError(f"Constraint '{constraint.id}' already exists in the configuration.")
        self.constraints[constraint.id] = constraint

    def remove_constraint(self, constraint_id: str) -> None:
        """
        Remove a constraint from the configuration.
        """
        if constraint_id not in self.constraints:
            raise ValueError(f"Constraint '{constraint_id}' does not exist in the configuration.")
        del self.constraints[constraint_id]

    def update_constraint(self, constraint: BindingConstraintSection) -> None:
        """
        Update an existing constraint in the configuration.
        """
        if constraint.id not in self.constraints:
            raise ValueError(f"Constraint '{constraint.id}' does not exist in the configuration.")
        self.constraints[constraint.id] = constraint

    def get_constraint(self, constraint_id: str) -> BindingConstraintSection:
        """
        Get a constraint from the configuration.
        """
        if constraint_id not in self.constraints:
            raise ValueError(f"Constraint '{constraint_id}' does not exist in the configuration.")
        return self.constraints[constraint_id]
