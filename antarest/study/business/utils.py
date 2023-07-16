import json
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    TypedDict,
    TypeVar,
)

import pydantic.error_wrappers
import pydantic.fields
import pydantic.main
import pydantic.utils
from antarest.core.exceptions import CommandApplicationError
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.requests import RequestParameters
from antarest.core.utils.string import to_camel_case
from antarest.study.model import RawStudy, Study
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.utils import is_managed
from antarest.study.storage.variantstudy.business.utils import (
    transform_command_to_dto,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from pydantic import BaseModel, Extra, ValidationError

# noinspection SpellCheckingInspection
GENERAL_DATA_PATH = "settings/generaldata"


def execute_or_add_commands(
    study: Study,
    file_study: FileStudy,
    commands: Sequence[ICommand],
    storage_service: StudyStorageService,
) -> None:
    if isinstance(study, RawStudy):
        executed_commands: List[ICommand] = []
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


# ====================================================================
#  Utility classes and function to make all Pydantic fields optionals
# ====================================================================


class AllOptionalMetaclass(pydantic.main.ModelMetaclass):
    """
    Metaclass that makes all fields of a Pydantic model optional.

    This metaclass modifies the class's annotations to make all fields
    optional by wrapping them with the `Optional` type.

    Usage:
        class MyModel(BaseModel, metaclass=AllOptionalMetaclass):
            field1: str
            field2: int
            ...

    The fields defined in the model will be automatically converted to optional
    fields, allowing instances of the model to be created even if not all fields
    are provided during initialization.
    """

    def __new__(
        cls: Type["AllOptionalMetaclass"],
        name: str,
        bases: Tuple[Type[Any], ...],
        namespaces: Dict[str, Any],
        **kwargs: Dict[str, Any],
    ) -> Any:
        annotations = namespaces.get("__annotations__", {})

        # Merge annotations from base classes
        for base in bases:
            annotations.update(getattr(base, "__annotations__", {}))

        # Convert fields to optional
        for field in annotations:
            if not field.startswith("__"):
                annotations[field] = Optional[annotations[field]]

        # Update the class's annotations
        namespaces["__annotations__"] = annotations

        return super().__new__(cls, name, bases, namespaces, **kwargs)


def create_field(
    default: Any = pydantic.fields.Undefined,
    *,
    default_factory: Optional[pydantic.fields.NoArgAnyCallable] = None,  # type: ignore
    **kwargs: Any,
) -> Any:
    """
    Create an optional Pydantic field.
    """
    if (
        default in {pydantic.fields.Undefined, pydantic.fields.Required}
        and default_factory is None
    ):
        return pydantic.fields.Field(None, ini_required=True, **kwargs)
    elif default_factory is None:
        return pydantic.fields.Field(
            None,
            ini_default=default,
            default_factory=default_factory,
            **kwargs,
        )
    else:
        return pydantic.fields.Field(
            pydantic.fields.Undefined,
            ini_default=default,
            default_factory=default_factory,
            **kwargs,
        )


Field = create_field


# ==============================================================
#  Helper fonctions to get/set values from/to a dictionary tree
# ==============================================================


def _get_tree_value(
    tree: Dict[str, Any], path: str, default: Any = None
) -> Any:
    """
    Retrieves the value of a dictionary tree based on a given path.
    """
    for key in path.split("/"):
        if key in tree:
            tree = tree[key]
        else:
            return default
    return tree


def _set_tree_value(tree: Dict[str, Any], path: str, value: Any) -> None:
    """
    Update or set the value of a dictionary tree based on a given path.
    """
    parts = path.split("/")
    for part in parts[:-1]:
        if part not in tree:
            tree[part] = {}
        tree = tree[part]
    tree[parts[-1]] = value


# ==============================================================
#  FormFieldsBaseModel model with support for INI configuration
# ==============================================================

# A variable annotated with "M" can only be an instance of `FormFieldsBaseModel`
# or an instance of a class inheriting from `FormFieldsBaseModel`.
M = TypeVar("M", bound="FormFieldsBaseModel")


class FormFieldsBaseModel(BaseModel):
    """
    Pydantic Model for webapp form
    """

    class Config:
        alias_generator = to_camel_case
        extra = Extra.forbid

    @classmethod
    def from_ini(
        cls: Type[M], ini_attrs: Dict[str, Any], study_version: int
    ) -> M:
        """
        Creates an instance of `FormFieldsBaseModel` from the given INI attributes.

        The conversion between the attribute names and the field names is ensured
        by the presence of an `ini_path` property when defining each field.

        The model construction must take into account the study version.
        The `start_version` and `end_version` properties can be defined in the
        `Config` class of the model to specify an availability interval to be applied
        by default for all fields. In order to specify the specific availability
        interval for each field, the properties can be set in the field.

        Example:

            class ThermalFormFields(FormFieldsBaseModel):
                ...
                must_run: bool = Field(False, ini_path="must-run")
                nh3: float = Field(0.0, ge=0, start_version=860)

        Args:
            cls: The class itself, or any subclass.
            ini_attrs: A dictionary containing the INI attributes to use for constructing the instance.
            study_version: Version of the current study.

        Returns:
            An instance of `FormFieldsBaseModel`.

        Raises:
            ValidationError: If there are extra fields not permitted.
        """
        # sourcery skip: low-code-quality
        model_start_ver: int = getattr(cls.Config, "start_version", 0)
        model_end_ver: int = getattr(cls.Config, "end_version", 0)
        fields_values = {}
        err_wrappers = []
        for field_name, field in cls.__fields__.items():
            # Extract the properties from the `field_info.extra` values
            extra = field.field_info.extra
            ini_path: str = extra.get("ini_path", field_name)
            ini_default: str = extra.get("ini_default", field.default)
            ini_required: bool = extra.get("ini_required", False)
            start_ver: int = extra.get("start_version", 0) or model_start_ver
            end_ver: int = extra.get("end_version", 0) or model_end_ver

            # Get the field value from the `ini_attrs`
            is_available = (
                start_ver <= study_version <= end_ver
                if end_ver
                else start_ver <= study_version
            )
            if ini_required:
                field_value = _get_tree_value(ini_attrs, ini_path)
            else:
                default = (
                    (
                        field.default_factory()  # type: ignore
                        if ini_default is None
                        else pydantic.utils.smart_deepcopy(ini_default)
                    )
                    if is_available
                    else None
                )
                field_value = _get_tree_value(
                    ini_attrs, ini_path, default=default
                )

            # Check the field value according to its availability
            if is_available:
                if field.required and field_value is None:
                    err_wrappers.append(
                        pydantic.error_wrappers.ErrorWrapper(
                            ValueError(
                                f"Required parameter '{ini_path}' is missing"
                            ),
                            loc=field_name,
                        )
                    )
            elif field_value is not None:
                err_wrappers.append(
                    pydantic.error_wrappers.ErrorWrapper(
                        ValueError(
                            f"Parameter '{ini_path}' is not available in the study version {study_version}"
                        ),
                        loc=field_name,
                    )
                )
            fields_values[field_name] = field_value

        # Report an error for each unknown `ini_path`
        known_paths: Set[str] = {
            field.field_info.extra.get("ini_path", name)
            for name, field in cls.__fields__.items()
        }
        err_wrappers.extend(
            pydantic.error_wrappers.ErrorWrapper(
                ValueError(f"Parameter '{ini_path}' is unknown"), loc=ini_path
            )
            for ini_path in ini_attrs
            if ini_path not in known_paths
        )

        if err_wrappers:
            raise ValidationError(err_wrappers, cls)

        return cls(**fields_values)

    def to_ini(self, study_version: int) -> Dict[str, Any]:
        model_start_ver: int = getattr(self.Config, "start_version", 0)
        model_end_ver: int = getattr(self.Config, "end_version", 0)
        fields_values = json.loads(self.json(by_alias=False))
        ini_attrs: Dict[str, Any] = {}
        err_wrappers = []
        for field_name, field in self.__fields__.items():
            # Extract the properties from the `field_info.extra` values
            extra = field.field_info.extra
            ini_path: str = extra.get("ini_path", field_name)
            start_ver: int = extra.get("start_version", 0) or model_start_ver
            end_ver: int = extra.get("end_version", 0) or model_end_ver

            # Set the field value to the `ini_attrs`
            is_available = (
                start_ver <= study_version <= end_ver
                if end_ver
                else start_ver <= study_version
            )
            field_value = fields_values.get(field_name)

            if is_available:
                if field.required and field_value is None:
                    err_wrappers.append(
                        pydantic.error_wrappers.ErrorWrapper(
                            ValueError(
                                f"Required parameter '{ini_path}' is missing"
                            ),
                            loc=field_name,
                        )
                    )
            elif field_value is not None:
                err_wrappers.append(
                    pydantic.error_wrappers.ErrorWrapper(
                        ValueError(
                            f"Parameter '{ini_path}' is not available in the study version {study_version}"
                        ),
                        loc=field_name,
                    )
                )

            if field_value is not None:
                _set_tree_value(ini_attrs, ini_path, field_value)

        if err_wrappers:
            raise ValidationError(err_wrappers, self.__class__)

        return ini_attrs


class FieldInfo(TypedDict, total=False):
    path: str
    default_value: Any
    start_version: Optional[int]
    end_version: Optional[int]
    # Workaround to replace Pydantic's computed values which are ignored by FastAPI.
    # TODO: check @computed_field available in Pydantic v2 to remove it
    # (value) -> encoded_value
    encode: Optional[Callable[[Any], Any]]
    # (encoded_value, current_value) -> decoded_value
    decode: Optional[Callable[[Any, Optional[Any]], Any]]
