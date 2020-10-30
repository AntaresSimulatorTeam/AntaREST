import abc
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

        self.build()

    def get_url(self) -> str:
        return self._parent.get_url() + "/" + self._key

    @abc.abstractmethod
    def build(self) -> None:
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
        self.build()

    def get_url(self) -> str:
        return self._root_url

    def build(self) -> None:

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

        self.build_children()

    def build_children(self) -> None:

        properties = self._jsm.get_properties()

        for key in properties:

            self._node_factory.build(
                key=key,
                jsm=self._jsm.get_child(key),
                parent=self,
            )

    def get_content(self) -> JSON:
        return self._swagger.json()


class PathNode(INode):
    def build(self) -> None:
        path = self.get_path()
        self._swagger.add_path(path)
        self.build_children()

    def build_children(self) -> None:

        if self._jsm.has_properties():

            properties = self._jsm.get_properties()
            for key in properties:
                self._node_factory.build(
                    key=key,
                    jsm=self._jsm.get_child(key),
                    parent=self,
                )

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


class FileNode(INode):
    def build(self) -> None:
        pass


class EmptyNode(INode):
    def build(self) -> None:
        pass

    def build_children(self) -> None:
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
        node_class: Type[INode] = EmptyNode

        if jsm.is_object():
            node_class = PathNode
        elif jsm.is_value():
            node_class = PathNode

        return node_class
