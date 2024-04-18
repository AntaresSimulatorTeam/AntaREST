import typing as t

import pydantic.fields
import pydantic.main
from pydantic import BaseModel

from antarest.core.utils.string import to_camel_case


class AllOptionalMetaclass(pydantic.main.ModelMetaclass):
    """
    Metaclass that makes all fields of a Pydantic model optional.

    Usage:
        class MyModel(BaseModel, metaclass=AllOptionalMetaclass):
            field1: str
            field2: int
            ...

    Instances of the model can be created even if not all fields are provided during initialization.
    Default values, when provided, are used unless `use_none` is set to `True`.
    """

    def __new__(
        cls: t.Type["AllOptionalMetaclass"],
        name: str,
        bases: t.Tuple[t.Type[t.Any], ...],
        namespaces: t.Dict[str, t.Any],
        use_none: bool = False,
        **kwargs: t.Dict[str, t.Any],
    ) -> t.Any:
        """
        Create a new instance of the metaclass.

        Args:
            name: Name of the class to create.
            bases: Base classes of the class to create (a Pydantic model).
            namespaces: namespace of the class to create that defines the fields of the model.
            use_none: If `True`, the default value of the fields is set to `None`.
                Note that this field is not part of the Pydantic model, but it is an extension.
            **kwargs: Additional keyword arguments used by the metaclass.
        """
        # Modify the annotations of the class (but not of the ancestor classes)
        # in order to make all fields optional.
        # If the current model inherits from another model, the annotations of the ancestor models
        # are not modified, because the fields are already converted to `ModelField`.
        annotations = namespaces.get("__annotations__", {})
        for field_name, field_type in annotations.items():
            if not field_name.startswith("__"):
                # Making already optional fields optional is not a problem (nothing is changed).
                annotations[field_name] = t.Optional[field_type]
        namespaces["__annotations__"] = annotations

        if use_none:
            # Modify the namespace fields to set their default value to `None`.
            for field_name, field_info in namespaces.items():
                if isinstance(field_info, pydantic.fields.FieldInfo):
                    field_info.default = None
                    field_info.default_factory = None

        # Create the class: all annotations are converted into `ModelField`.
        instance = super().__new__(cls, name, bases, namespaces, **kwargs)

        # Modify the inherited fields of the class to make them optional
        # and set their default value to `None`.
        model_field: pydantic.fields.ModelField
        for field_name, model_field in instance.__fields__.items():
            model_field.required = False
            model_field.allow_none = True
            if use_none:
                model_field.default = None
                model_field.default_factory = None
                model_field.field_info.default = None

        return instance


MODEL = t.TypeVar("MODEL", bound=t.Type[BaseModel])


def camel_case_model(model: MODEL) -> MODEL:
    """
    This decorator can be used to modify a model to use camel case aliases.

    Args:
        model: The pydantic model to modify.

    Returns:
        The modified model.
    """
    model.__config__.alias_generator = to_camel_case
    for field_name, field in model.__fields__.items():
        field.alias = to_camel_case(field_name)
    return model
