import json
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    Type,
    TypedDict,
    TypeVar,
)

from pydantic import BaseModel, Extra

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


# A variable annotated with T can only be an instance of `FormFieldsBaseModel`
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
    def from_ini(cls: Type[M], ini_attrs: Dict[str, Any]) -> M:
        """
        Creates an instance of `FormFieldsBaseModel` from the given INI attributes.

        The conversion between the attribute names and the field names is ensured
        by the presence of an `ini_alias` attribute when defining each field:

        Example:

            class ThermalFormFields(FormFieldsBaseModel):
                ...
                must_run: bool = Field(False, ini_alias="must-run")

        Args:
            cls: The class itself, or any subclass.
            ini_attrs: A dictionary containing the INI attributes to use for constructing the instance.

        Returns:
            An instance of `FormFieldsBaseModel`.

        Raises:
            ValidationError: If there are extra fields not permitted.
        """
        aliases = {
            field.field_info.extra.get("ini_alias", name): name
            for name, field in cls.__fields__.items()
        }
        fields_values = {
            aliases.get(ini_name, ini_name): value
            for ini_name, value in ini_attrs.items()
        }
        return cls.construct(**fields_values)

    def to_ini(self) -> Dict[str, Any]:
        """
        Converts the instance of `FormFieldsBaseModel` to a dictionary of INI attributes.

        In the INI file, there are only required values or non-default values.

        The conversion between the field names and the attribute names is ensured
        by the presence of an `ini_alias` attribute when defining each field.

        Example:

            class ThermalFormFields(FormFieldsBaseModel):
                ...
                must_run: bool = Field(False, ini_alias="must-run")

        Returns:
            A dictionary of INI attributes.
        """
        fields_values = json.loads(self.json(by_alias=False))
        ini_attrs = {}
        for name, field in self.__fields__.items():
            ini_alias = field.field_info.extra.get("ini_alias", name)
            value = fields_values[name]
            if field.required or value != field.get_default():
                ini_attrs[ini_alias] = value
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
