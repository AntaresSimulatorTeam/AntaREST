import abc
from pathlib import Path
from typing import Type

from api_iso_antares.custom_types import JSON
from api_iso_antares.engine.swagger.swagger import (
    Swagger,
    SwaggerOperation,
    SwaggerParameter,
    SwaggerPath,
    SwaggerTag,
)
from api_iso_antares.jsm import JsonSchema


class INode(abc.ABC):
    def __init__(
        self,
        key: str,
        jsm: JsonSchema,
        node_factory: "NodeFactory",
        parent: "INode",
    ) -> None:
        self._key = key
        self._jsm = jsm
        self._node_factory = node_factory
        self._parent = parent
        self._swagger: Swagger = self._parent._swagger

    def get_url(self) -> str:
        return str(Path(self._parent.get_url()) / self._key)

    @abc.abstractmethod
    def build_content(self) -> None:
        pass


class RootNode(INode):
    def __init__(
        self,
        jsm: JsonSchema,
    ) -> None:

        self._jsm = jsm
        self._node_factory = NodeFactory()
        self._swagger = Swagger()
        self._root_url: str = "/metadata/{study}"

    def get_url(self) -> str:
        return self._root_url

    def build_swagger(self) -> None:

        study_path = SwaggerPath(url=self._root_url)
        study_path.add_parameter(
            SwaggerParameter(
                name="study",
                where=SwaggerParameter.ParametersIn.path,
                description="Study name",
            )
        )
        study_path.add_operation(
            SwaggerOperation(verb=SwaggerOperation.OperationVerbs.get)
        )

        for key in self._jsm.get_properties():
            self._swagger.add_tag(SwaggerTag(key))

        self._swagger.add_path(study_path)

    def build_content(self) -> None:
        self.build_swagger()

        properties = self._jsm.get_properties()

        for key in properties:

            child_node = self._node_factory.build(
                key=key,
                jsm=self._jsm.get_child(key),
                parent=self,
            )

            child_node.build_content()

    def get_content(self) -> JSON:
        self.build_content()
        return self._swagger.json()


class PathNode(INode):
    def build_content(self) -> None:

        self.build_swagger()

        properties = self._jsm.get_properties()

        for key in properties:
            child_node = self._node_factory.build(
                key=key,
                jsm=self._jsm.get_child(key),
                parent=self,
            )

            child_node.build_content()

    def build_swagger(self) -> None:
        self._swagger.add_path(self.get_path())

    def get_path(self) -> SwaggerPath:
        swagger_path = SwaggerPath(url=self.get_url())

        operation_get = SwaggerOperation(
            verb=SwaggerOperation.OperationVerbs.get
        )
        operation_get.add_tag(self._get_tag())
        swagger_path.add_operation(operation_get)

        return swagger_path

    def _get_tag(self) -> str:
        return self.get_url().split("/")[3]


class EmptyNode(INode):
    def build_content(self) -> None:
        pass


class NodeFactory:
    def build(
        self,
        key: str,
        jsm: JsonSchema,
        parent: INode,
    ) -> INode:
        node_class = NodeFactory.get_node_class_by_strategy(jsm)
        return node_class(
            key=key,
            jsm=jsm,
            node_factory=self,
            parent=parent,
        )

    @staticmethod
    def get_node_class_by_strategy(jsm: JsonSchema) -> Type[INode]:
        if jsm.is_object():
            return PathNode
        return EmptyNode
