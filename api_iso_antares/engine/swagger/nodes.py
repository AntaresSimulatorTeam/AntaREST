from typing import List

from api_iso_antares.custom_types import JSON
from api_iso_antares.engine.swagger.swagger import (
    Swagger,
    SwaggerOperation,
    SwaggerOperationBuilder,
    SwaggerParameter,
    SwaggerParameterBuilder,
    SwaggerPath,
    SwaggerPathBuilder,
    SwaggerTag,
)
from api_iso_antares.jsm import JsonSchema


class RootNode:
    def __init__(
        self,
        jsm: JsonSchema,
    ) -> None:

        self.jsm = jsm
        self.swagger = Swagger()
        self.url: str = "/studies/{uuid}"

        self._build()

    def get_content(self) -> JSON:
        return self.swagger.json()

    def build_and_add_path(
        self,
        url: str,
        operations: List[SwaggerOperation] = [],
        parameters: List[SwaggerParameter] = [],
    ) -> None:
        swagger_path = SwaggerPathBuilder.build(
            url=url, operations=operations, parameters=parameters
        )
        self.swagger.add_path(swagger_path)

    def _build(self) -> None:
        self._add_tags()
        self._build_global_parameters()
        self._build_paths_from_jsm()
        self._build_paths_not_in_jsm()

    def _add_tags(self) -> None:
        for key in self.jsm.get_properties():
            self.swagger.add_tag(SwaggerTag(key))

    def _build_global_parameters(self) -> None:

        depth_parameter = SwaggerParameter(
            name="depth",
            in_=SwaggerParameter.ParametersIn.query,
            schema_type=SwaggerParameter.SchemaType.integer,
            required=False,
        )

        self.swagger.add_global_parameters(depth_parameter)

    def _build_paths_not_in_jsm(self) -> None:
        self._build_study_path()
        self._build_studies_path()
        self._build_copy_study_path()
        self._build_export_path()
        self._build_files_path()

    def _build_study_path(self) -> None:

        url = self.url
        operations = [
            SwaggerOperationBuilder.post(),
            SwaggerOperationBuilder.get(),
            SwaggerOperationBuilder.delete(),
        ]

        self.build_and_add_path(url=url, operations=operations)

    def _build_studies_path(self) -> None:

        url = "/studies"
        operations = [
            SwaggerOperationBuilder.get(),
            SwaggerOperationBuilder.post_with_binary_data(),
        ]

        self.build_and_add_path(url=url, operations=operations)

    def _build_copy_study_path(self) -> None:
        url = self.url + "/copy"
        operations = [SwaggerOperationBuilder.post()]
        parameters = [SwaggerParameterBuilder.build_query("dest")]

        self.build_and_add_path(
            url=url, operations=operations, parameters=parameters
        )

    def _build_export_path(self) -> None:

        url = "/studies/{uuid}/export"
        operations = [SwaggerOperationBuilder.get()]
        parameters = [
            SwaggerParameterBuilder.build_query(name="compact", required=False)
        ]

        self.build_and_add_path(
            url=url, operations=operations, parameters=parameters
        )

    def _build_files_path(self) -> None:

        url = "/file/{path}"
        operations = [
            SwaggerOperationBuilder.get(),
            SwaggerOperationBuilder.post_with_binary_data(),
        ]

        self.build_and_add_path(url=url, operations=operations)

    def _build_paths_from_jsm(self) -> None:

        properties = self.jsm.get_properties()

        for key in properties:

            PathNode(
                url=self.url + "/" + key,
                jsm=self.jsm.get_child(key),
                swagger=self.swagger,
            )


class PathNode:
    def __init__(self, url: str, jsm: JsonSchema, swagger: Swagger) -> None:
        self.url = url
        self.jsm = jsm
        self.swagger: swagger = swagger

        self._build()

    def _build(self) -> None:

        path = self._get_swagger_path()
        self.swagger.add_path(path)

        if not self._is_leaf():
            self._build_children()

    def _is_leaf(self) -> bool:
        return self.jsm.is_swagger_leaf()

    def _get_swagger_path(self) -> SwaggerPath:

        operation = SwaggerOperationBuilder.get()
        operation.add_tag(self._get_tag())
        operations = [operation]

        swagger_path = SwaggerPathBuilder.build(
            url=self.url,
            operations=operations,
        )

        return swagger_path

    def _build_children(self) -> None:
        self._build_children_property_based()
        self._build_children_additional_property_based()

    def _build_children_property_based(self) -> None:
        if self.jsm.has_properties():

            properties = self.jsm.get_properties()
            for key in properties:
                PathNode(
                    url=self.url + "/" + key,
                    jsm=self.jsm.get_child(key),
                    swagger=self.swagger,
                )

    def _build_children_additional_property_based(self) -> None:
        if self.jsm.has_defined_additional_properties():

            jsm = self.jsm.get_additional_properties()
            key = self._get_additional_property_name()

            PathNode(url=self.url + "/" + key, jsm=jsm, swagger=self.swagger)

    def _get_additional_property_name(self) -> str:
        return "{" + self.jsm.get_additional_property_name() + "}"

    def _get_tag(self) -> str:
        return self.url.split("/")[3]
