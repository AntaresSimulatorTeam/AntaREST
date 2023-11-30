import typing as t

from pydantic import BaseModel, Extra, Field, root_validator

__all__ = ("IgnoreCaseIdentifier", "LowerCaseIdentifier")


class IgnoreCaseIdentifier(
    BaseModel,
    extra=Extra.forbid,
    validate_assignment=True,
    allow_population_by_field_name=True,
):
    """
    Base class for all configuration sections with an ID.
    """

    id: str = Field(description="ID (section name)", regex=r"[a-zA-Z0-9_(),& -]+")

    @classmethod
    def generate_id(cls, name: str) -> str:
        """
        Generate an ID from a name.

        Args:
            name: Name of a section read from an INI file

        Returns:
            The ID of the section.
        """
        # Avoid circular imports
        from antarest.study.storage.rawstudy.model.filesystem.config.model import transform_name_to_id

        return transform_name_to_id(name, lower=False)

    @root_validator(pre=True)
    def validate_id(cls, values: t.MutableMapping[str, t.Any]) -> t.Mapping[str, t.Any]:
        """
        Calculate an ID based on the name, if not provided.

        Args:
            values: values used to construct the object.

        Returns:
            The updated values.
        """
        if storage_id := values.get("id"):
            # If the ID is provided, it comes from a INI section name.
            # In some legacy case, the ID was in lower case, so we need to convert it.
            values["id"] = cls.generate_id(storage_id)
            return values
        if not values.get("name"):
            return values
        name = values["name"]
        if storage_id := cls.generate_id(name):
            values["id"] = storage_id
        else:
            raise ValueError(f"Invalid name '{name}'.")
        return values


class LowerCaseIdentifier(IgnoreCaseIdentifier):
    """
    Base class for all configuration sections with a lower case ID.
    """

    id: str = Field(description="ID (section name)", regex=r"[a-z0-9_(),& -]+")

    @classmethod
    def generate_id(cls, name: str) -> str:
        """
        Generate an ID from a name.

        Args:
            name: Name of a section read from an INI file

        Returns:
            The ID of the section.
        """
        # Avoid circular imports
        from antarest.study.storage.rawstudy.model.filesystem.config.model import transform_name_to_id

        return transform_name_to_id(name, lower=True)
