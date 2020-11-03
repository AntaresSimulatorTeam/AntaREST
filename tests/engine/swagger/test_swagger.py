from unittest.mock import Mock

import pytest

from api_iso_antares.engine.swagger.swagger import (
    ISwaggerElement,
    Swagger,
    SwaggerOperation,
    SwaggerParameter,
    SwaggerPath,
    SwaggerResponse,
)


@pytest.mark.unit_test
def test_format_key() -> None:
    assert "ini" == ISwaggerElement.format_key("ini_")


@pytest.mark.unit_test
def test_value_to_json() -> None:
    def launch_test(value, result) -> None:
        assert ISwaggerElement.value_to_json(value) == result

    launch_test(value=None, result=None)

    swagger_element = Mock()
    swagger_element.__class__ = ISwaggerElement
    result = {"ex1": "value_ex1"}
    swagger_element.json.return_value = result
    launch_test(value=swagger_element, result=result)

    launch_test(value=result, result=result)

    value = {"ex2": swagger_element}
    result = {"ex2": {"ex1": "value_ex1"}}
    launch_test(value=value, result=result)

    value = [swagger_element]
    result = [{"ex1": "value_ex1"}]
    launch_test(value=value, result=result)


@pytest.mark.unit_test
def test_swagger_response() -> None:
    responses = SwaggerResponse.get_defaults([200])
    assert responses["200"]._code == 200


@pytest.mark.unit_test
def test_swagger_operation() -> None:
    verb = SwaggerOperation.OperationVerbs.get
    operation = SwaggerOperation(verb=verb)
    assert operation._verb == verb
    assert operation.responses["200"]["description"] == "Successful operation"


@pytest.mark.unit_test
def test_swagger_parameter() -> None:

    param_in = SwaggerParameter.ParametersIn.path
    parameter = SwaggerParameter(name="ex1", where=param_in)

    assert parameter.in_ == param_in.name
    assert parameter.schema == {"type": "string"}
    assert parameter.is_path_parameter()


@pytest.mark.unit_test
def test_swagger_path() -> None:
    path = SwaggerPath(url="/toto/tata")

    verb = SwaggerOperation.OperationVerbs.get
    operation = Mock()
    operation._verb = verb
    path.add_operation(operation)
    assert path.get is operation

    parameter = Mock()
    parameter.is_path_parameter.return_value = True
    path.add_parameters([parameter])

    assert len(path.parameters) == 1

    sub_parameters = path.get_path_parameters()
    assert len(sub_parameters) == 1

    parameter = Mock()
    parameter.is_path_parameter.return_value = False
    path.add_parameter(parameter)
    sub_parameters = path.get_path_parameters()
    assert len(sub_parameters) == 1


@pytest.mark.unit_test
def test_swagger() -> None:
    swagger = Swagger()
    swagger_json = swagger.json()

    assert swagger_json["openapi"] == "3.0.0"

    path = SwaggerPath(url="/{toto}")

    parameter1 = Mock()
    parameter1.is_path_parameter.return_value = True

    parameter2 = Mock()
    parameter2.is_path_parameter.return_value = False
    path.add_parameters([parameter1, parameter2])

    swagger.add_path(path)

    path_child = SwaggerPath(url="/{toto}/tata")
    swagger.add_path(path_child)

    assert len(path_child.parameters) == 1
