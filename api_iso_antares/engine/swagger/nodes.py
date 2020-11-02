import abc
from typing import Any, Dict, Optional, Tuple, Type

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

        self._build()

    def get_url(self) -> str:
        return self._parent.get_url() + "/" + self._key

    @abc.abstractmethod
    def _build(self) -> None:
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
        self._build()

    def get_url(self) -> str:
        return self._root_url

    def get_content(self) -> JSON:
        return self._swagger.json()

    def _build(self) -> None:
        self._build_study_path()
        self._build_global_parameters()
        self._build_children()

    def _build_study_path(self) -> None:

        study_path = SwaggerPath(url=self._root_url)

        study_path.add_operation(
            SwaggerOperation(verb=SwaggerOperation.OperationVerbs.get)
        )
        for key in self._jsm.get_properties():
            self._swagger.add_tag(SwaggerTag(key))

        self._swagger.add_path(study_path)

    def _build_global_parameters(self) -> None:

        depth_parameter = SwaggerParameter(
            name="depth",
            where=SwaggerParameter.ParametersIn.query,
            schema_type=SwaggerParameter.SchemaType.integer,
            required=False,
        )

        self._swagger.add_global_parameters(depth_parameter)

    def _build_children(self) -> None:

        properties = self._jsm.get_properties()

        for key in properties:

            self._node_factory.build(
                key=key,
                jsm=self._jsm.get_child(key),
                parent=self,
            )


class PathNode(INode):
    def _build(self) -> None:
        self._build_path()
        self._build_children()

    def _build_path(self) -> None:
        path = self._get_path()
        self._swagger.add_path(path)

    def _build_children(self) -> None:
        self._build_children_property_based()
        self._build_children_additional_property_based()

    def _build_children_property_based(self) -> None:
        if self._jsm.has_properties():

            properties = self._jsm.get_properties()
            for key in properties:
                self._node_factory.build(
                    key=key,
                    jsm=self._jsm.get_child(key),
                    parent=self,
                )

    def _build_children_additional_property_based(self) -> None:
        if self._jsm.has_defined_additional_properties():

            jsm = self._jsm.get_additional_properties()
            key = "{" + self._jsm.get_additional_property_name() + "}"

            self._node_factory.build(key, jsm=jsm, parent=self)

    def _get_path(self) -> SwaggerPath:

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
    def _build(self) -> None:
        # Nothing should end up here if Swagger is complete.
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

        if jsm.is_object() or jsm.is_value():
            node_class = PathNode

        return node_class
