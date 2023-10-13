import typing as t

from pydantic import BaseModel, Extra, Field, root_validator


class SectionConfig(
    BaseModel,
    extra=Extra.forbid,
    validate_assignment=True,
    allow_population_by_field_name=True,
):
    """
    Base class for all configuration sections.
    """

    id: str = Field(
        description="ID (section name)",
        regex=r"[a-zA-Z0-9_(),& -]+",
    )

    @root_validator(pre=True)
    def generate_id(cls, values: t.MutableMapping[str, t.Any]) -> t.Mapping[str, t.Any]:
        """
        Calculate an ID based on the name, if not provided.

        Args:
            values: values used to construct the object.

        Returns:
            The updated values.
        """
        # Avoid circular imports
        from antarest.study.storage.rawstudy.model.filesystem.config.model import transform_name_to_id

        if storage_id := values.get("id"):
            # If the ID is provided, it comes from a INI section name.
            # In some legacy case, the ID was in lower case, so we need to convert it.
            values["id"] = transform_name_to_id(storage_id)
            return values
        if not values.get("name"):
            return values
        name = values["name"]
        if storage_id := transform_name_to_id(name):
            values["id"] = storage_id
        else:
            raise ValueError(f"Invalid name '{name}'.")
        return values
