import json
import typing as t

from pydantic import BaseModel, Extra


class IniProperties(
    BaseModel,
    # On reading, if the configuration contains an extra field, it is better
    # to forbid it, because it allows errors to be detected early.
    # Ignoring extra attributes can hide errors.
    extra=Extra.forbid,
    # If a field is updated on assignment, it is also validated.
    validate_assignment=True,
    # On testing, we can use snake_case for field names.
    allow_population_by_field_name=True,
):
    """
    Base class for configuration sections.
    """

    def to_config(self) -> t.Mapping[str, t.Any]:
        """
        Convert the object to a dictionary for writing to a configuration file (`*.ini`).

        Returns:
            A dictionary with the configuration values.
        """

        config = {}
        for field_name, field in self.__fields__.items():
            value = getattr(self, field_name)
            if value is None:
                continue
            if isinstance(value, IniProperties):
                config[field.alias] = value.to_config()
            else:
                config[field.alias] = json.loads(json.dumps(value))
        return config

    @classmethod
    def construct(cls, _fields_set: t.Optional[t.Set[str]] = None, **values: t.Any) -> "IniProperties":
        """
        Construct a new model instance from a dict of values, replacing aliases with real field names.
        """
        # The pydantic construct() function does not allow aliases to be handled.
        aliases = {(field.alias or name): name for name, field in cls.__fields__.items()}
        renamed_values = {aliases.get(k, k): v for k, v in values.items()}
        if _fields_set is not None:
            _fields_set = {aliases.get(f, f) for f in _fields_set}
        # noinspection PyTypeChecker
        return super().construct(_fields_set, **renamed_values)
