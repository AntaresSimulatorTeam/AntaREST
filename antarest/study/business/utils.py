import typing as t

import pydantic.fields
import pydantic.main
from pydantic import BaseModel

from antarest.core.exceptions import CommandApplicationError
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.requests import RequestParameters
from antarest.core.utils.string import to_camel_case
from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.model import RawStudy, Study
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.utils import is_managed
from antarest.study.storage.variantstudy.business.utils import transform_command_to_dto
from antarest.study.storage.variantstudy.model.command.icommand import ICommand

# noinspection SpellCheckingInspection
GENERAL_DATA_PATH = "settings/generaldata"


class ClusterType(EnumIgnoreCase):
    ST_STORAGE = "storages"
    RENEWABLE = "renewable"
    THERMAL = "thermal"


def execute_or_add_commands(
    study: Study,
    file_study: FileStudy,
    commands: t.Sequence[ICommand],
    storage_service: StudyStorageService,
) -> None:
    if isinstance(study, RawStudy):
        executed_commands: t.MutableSequence[ICommand] = []
        for command in commands:
            result = command.apply(file_study)
            if not result.status:
                raise CommandApplicationError(result.message)
            executed_commands.append(command)
        storage_service.variant_study_service.invalidate_cache(study)
        if not is_managed(study):
            # In a previous version, de-normalization was performed asynchronously.
            # However, this cause problems with concurrent file access,
            # especially when de-normalizing a matrix (which can take time).
            #
            # async_denormalize = threading.Thread(
            #     name=f"async_denormalize-{study.id}",
            #     target=file_study.tree.denormalize,
            # )
            # async_denormalize.start()
            #
            # To avoid this concurrency problem, it would be necessary to implement a
            # locking system for the entire study using a file lock (since multiple processes,
            # not only multiple threads, could access the same content simultaneously).
            #
            # Currently, we use a synchronous call to address the concurrency problem
            # within the current process (not across multiple processes)...
            file_study.tree.denormalize()
    else:
        storage_service.variant_study_service.append_commands(
            study.id,
            transform_command_to_dto(commands, force_aggregate=True),
            RequestParameters(user=DEFAULT_ADMIN_USER),
        )


class FormFieldsBaseModel(
    BaseModel,
    alias_generator=to_camel_case,
    extra="forbid",
    validate_assignment=True,
    allow_population_by_field_name=True,
):
    """
    Pydantic Model for webapp form
    """


class FieldInfo(t.TypedDict, total=False):
    path: str
    default_value: t.Any
    start_version: t.Optional[int]
    end_version: t.Optional[int]
    # Workaround to replace Pydantic computed values which are ignored by FastAPI.
    # TODO: check @computed_field available in Pydantic v2 to remove it
    # (value) -> encoded_value
    encode: t.Optional[t.Callable[[t.Any], t.Any]]
    # (encoded_value, current_value) -> decoded_value
    decode: t.Optional[t.Callable[[t.Any, t.Optional[t.Any]], t.Any]]


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
