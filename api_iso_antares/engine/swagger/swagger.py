import abc
import enum
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

from api_iso_antares.custom_types import JSON, SUB_JSON


class ISwaggerElement(abc.ABC):
    def json(self) -> JSON:
        output: JSON = dict()
        filtered_elements = self.get_filtered_elements()
        for key, value in filtered_elements:
            key_formatted = ISwaggerElement.format_key(key)
            output[key_formatted] = ISwaggerElement.value_to_json(value)
        return output

    ValueType = Union["ISwaggerElement", Dict[str, Any], List[Any]]

    def get_filtered_elements(self) -> Iterator[Tuple[str, ValueType]]:
        return filter(
            lambda item: ISwaggerElement.is_item_in_json(item[0], item[1]),
            self.__dict__.items(),
        )

    @staticmethod
    def format_key(key: str) -> str:
        if key[-1] == "_":
            key = key[:-1]
        return key

    @staticmethod
    def value_to_json(value: ValueType) -> SUB_JSON:
        if isinstance(value, ISwaggerElement):
            value = ISwaggerElement.swagger_element_to_json(value)
        elif isinstance(value, dict):
            value = ISwaggerElement.dict_to_json(value)
        elif isinstance(value, list):
            value = ISwaggerElement.list_to_json(value)
        return value

    @staticmethod
    def swagger_element_to_json(value: "ISwaggerElement") -> JSON:
        return value.json()

    @staticmethod
    def dict_to_json(value: Dict[str, Any]) -> Dict[str, Any]:
        output = {}
        for key, value in value.items():
            if isinstance(value, ISwaggerElement):
                value = value.json()
            output[key] = value
        return output

    @staticmethod
    def list_to_json(
        value: List[Union["ISwaggerElement", Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        output = []
        for elt in value:
            if isinstance(elt, ISwaggerElement):
                elt = elt.json()
            output.append(elt)
        return output

    @staticmethod
    def is_item_in_json(key: str, value: ValueType) -> bool:
        return bool(value) and not key.startswith("_")


class SwaggerResponse(ISwaggerElement):
    def __init__(
        self,
        code: int,
        description: Optional[str],
        content: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._code = code
        self.description = description
        self.content = content

    @staticmethod
    def get_default(code: int) -> "SwaggerResponse":

        default_values: Dict[int, Dict[str, Any]] = {
            200: {
                "description": "Successful operation",
                "content": {"application/json": {}},
            },
            400: {"description": "Invalid request"},
        }

        if code not in default_values:
            raise NotImplementedError("This code has no default values")

        description = default_values[code].get("description", None)
        return SwaggerResponse(
            code=code,
            description=description,
            content=default_values[code].get("content"),
        )

    @staticmethod
    def get_defaults(codes: List[int]) -> Dict[str, "SwaggerResponse"]:
        responses = {}
        for code in codes:
            responses[str(code)] = SwaggerResponse.get_default(code)
        return responses


class SwaggerOperation(ISwaggerElement):
    class OperationVerbs(enum.Enum):
        get = enum.auto()

    def __init__(
        self,
        verb: OperationVerbs,
        responses: Optional[Dict[str, SwaggerResponse]] = None,
    ) -> None:
        self._verb = verb
        if responses is None:
            self._responses = SwaggerResponse.get_defaults([200, 400])
        else:
            self._responses = responses

        self.tags: List[str] = []
        self.responses: Dict[str, Dict[str, Any]] = {}
        self._build_responses()

    def _build_responses(self) -> None:
        for code, response in self._responses.items():
            self.responses[code] = response.json()

    def add_tag(self, tag: str) -> None:
        self.tags.append(tag)


class SwaggerParameter(ISwaggerElement):
    class ParametersIn(enum.Enum):
        path = enum.auto()

    class SchemaType(enum.Enum):
        string = enum.auto()

    def __init__(
        self,
        name: str,
        where: ParametersIn,
        description: str = "",
        required: bool = True,
        schema_type: SchemaType = SchemaType.string,
    ) -> None:
        self.name = name
        self.in_ = where.name
        self.description = description
        self.required = required
        self.schema = {"type": schema_type.name}

    def is_path_parameter(self) -> bool:
        return self.in_ == SwaggerParameter.ParametersIn.path.name


class SwaggerPath(ISwaggerElement):
    def __init__(self, url: str) -> None:
        self.parameters: List[SwaggerParameter] = []
        self.get: Optional[SwaggerOperation] = None
        self._url = url

    def get_url(self) -> str:
        return self._url

    def get_parent_url(self) -> str:
        splitted_url = self.get_url().split("/")
        return "/".join(splitted_url[:-1])

    def add_operation(self, operation: SwaggerOperation) -> None:
        if operation._verb == SwaggerOperation.OperationVerbs.get:
            self.get = operation

    def add_parameter(self, parameter: SwaggerParameter) -> None:
        self.parameters.append(parameter)

    def add_parameters(self, parameters: List[SwaggerParameter]) -> None:
        self.parameters += parameters

    def get_path_parameters(self) -> List[SwaggerParameter]:
        path_parameters = []
        for parameter in self.parameters:
            if parameter.is_path_parameter():
                path_parameters.append(parameter)
        return path_parameters


class SwaggerTag(ISwaggerElement):
    def __init__(self, name: str, description: str = "") -> None:
        self.name = name
        self.description = description


class Swagger(ISwaggerElement):
    def __init__(self) -> None:
        self.openapi = "3.0.0"
        self.info = {
            "description": "API ANTARES",
            "version": "0.0.1",
            "title": "API ANTARES",
        }
        self.tags: List[SwaggerTag] = []
        self.paths: Dict[str, SwaggerPath] = dict()
        # TODO: add set_servers / Tech debt for the demo
        self.servers = [{"url": "http://0.0.0.0:8080"}]

    def add_tag(self, tag: SwaggerTag) -> None:
        self.tags.append(tag)

    def add_path(self, path: SwaggerPath) -> None:
        previous_path_parameters = self.get_previous_path_parameters(path)
        path.add_parameters(previous_path_parameters)
        self.paths[path.get_url()] = path

    def get_previous_path_parameters(
        self, path: SwaggerPath
    ) -> List[SwaggerParameter]:
        url_parent = path.get_parent_url()
        previous_path_parameters = []
        for prev_url, prev_path in self.paths.items():
            if url_parent == prev_url:
                previous_path_parameters = prev_path.get_path_parameters()
                break
        return previous_path_parameters
