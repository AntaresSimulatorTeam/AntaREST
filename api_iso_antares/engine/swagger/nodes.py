import abc
from typing import Type

from api_iso_antares.custom_types import JSON
from api_iso_antares.engine.swagger.swagger import (
    Swagger,
    SwaggerOperation,
    SwaggerParameter,
    SwaggerPath,
    SwaggerRequestBody,
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
        self._root_url: str = "/studies/{uuid}"
        self._build()

    def get_url(self) -> str:
        return self._root_url

    def get_content(self) -> JSON:
        return self._swagger.json()

    def _build(self) -> None:
        self._build_global_parameters()
        self._build_children()
        self._build_paths_not_in_jsm()
        self._add_tags()

    def _build_paths_not_in_jsm(self) -> None:
        self._build_studies_root()
        self._build_study_path()
        self._build_copy_study_path()
        self._build_export_path()
        self._build_files_path()

    def _build_copy_study_path(self) -> None:
        url = self._root_url + "/copy"

        copy_study_path = SwaggerPath(url=url)

        copy_study_path.add_operation(
            SwaggerOperation(verb=SwaggerOperation.OperationVerbs.post)
        )

        dest_parameter = SwaggerParameter(
            name="dest",
            in_=SwaggerParameter.ParametersIn.query,
        )

        copy_study_path.add_parameter(dest_parameter)

        self._swagger.add_path(copy_study_path)

    def _build_study_path(self) -> None:
        study_path = SwaggerPath(url=self._root_url)

        study_path.add_operation(
            SwaggerOperation(verb=SwaggerOperation.OperationVerbs.get)
        )
        study_path.add_operation(
            SwaggerOperation(verb=SwaggerOperation.OperationVerbs.post)
        )
        study_path.add_operation(
            SwaggerOperation(verb=SwaggerOperation.OperationVerbs.delete)
        )

        self._swagger.add_path(study_path)

    def _build_studies_root(self) -> None:
        studies_url = "/studies"
        study_path = SwaggerPath(url=studies_url)
        self._build_studies_list_path(study_path)
        self._build_import_study_path(study_path)
        self._swagger.add_path(study_path)

    @staticmethod
    def _build_import_study_path(study_path: SwaggerPath) -> None:

        post_operation = SwaggerOperation.get_default(
            SwaggerOperation.OperationVerbs.post
        )

        study_path.add_operation(post_operation)

    @staticmethod
    def _build_studies_list_path(study_path: SwaggerPath) -> None:
        study_path.add_operation(
            SwaggerOperation(verb=SwaggerOperation.OperationVerbs.get)
        )

    def _build_export_path(self) -> None:
        studies_url = "/studies/{uuid}/export"
        export_path = SwaggerPath(url=studies_url)

        export_path.add_operation(
            SwaggerOperation(verb=SwaggerOperation.OperationVerbs.get)
        )

        compact_parameter = SwaggerParameter(
            name="compact",
            in_=SwaggerParameter.ParametersIn.query,
            required=False,
        )

        export_path.add_parameter(compact_parameter)

        self._swagger.add_path(export_path)

    def _build_files_path(self) -> None:

        file_url = "/file/{path}"
        get_file_path = SwaggerPath(url=file_url)

        get_file_path.add_operation(
            SwaggerOperation(verb=SwaggerOperation.OperationVerbs.get)
        )

        post_operation = SwaggerOperation.get_default(
            SwaggerOperation.OperationVerbs.post
        )
        get_file_path.add_operation(post_operation)

        self._swagger.add_path(get_file_path)

    def _add_tags(self) -> None:
        for key in self._jsm.get_properties():
            self._swagger.add_tag(SwaggerTag(key))

    def _build_global_parameters(self) -> None:

        depth_parameter = SwaggerParameter(
            name="depth",
            in_=SwaggerParameter.ParametersIn.query,
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

        if not self._is_leaf():
            self._build_children_property_based()
            self._build_children_additional_property_based()

    def _is_leaf(self) -> bool:
        return self._jsm.is_swagger_leaf()

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
            key = self._get_additional_property_name()

            self._node_factory.build(key, jsm=jsm, parent=self)

    def _get_additional_property_name(self) -> str:
        return "{" + self._jsm.get_additional_property_name() + "}"

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


class NodeFactory:
    def build(
        self,
        key: str,
        jsm: JsonSchema,
        parent: INode,
    ) -> None:

        node_class = NodeFactory.get_node_class_by_strategy(jsm)

        node_class(
            key=key,
            jsm=jsm,
            node_factory=self,
            parent=parent,
        )

    @staticmethod
    def is_buildable_node(jsm: JsonSchema) -> bool:
        return not jsm.is_array()

    @staticmethod
    def get_node_class_by_strategy(jsm: JsonSchema) -> Type[INode]:

        node_class: Type[INode]
        if jsm.is_object() or jsm.is_value() or jsm.is_array():
            node_class = PathNode
        else:
            raise NotImplementedError(
                "The jsonschema format is not implemented."
            )

        return node_class
