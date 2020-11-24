from api_iso_antares.custom_types import JSON
from api_iso_antares.engine.swagger.swagger import (
    Swagger,
    SwaggerOperation,
    SwaggerParameter,
    SwaggerPath,
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

    def _build(self) -> None:
        self._build_global_parameters()
        self._build_paths_from_jsm()
        self._build_paths_not_in_jsm()
        self._add_tags()

    def _build_paths_not_in_jsm(self) -> None:
        self._build_studies_root()
        self._build_study_path()
        self._build_copy_study_path()
        self._build_export_path()
        self._build_files_path()

    def _build_studies_root(self) -> None:
        studies_url = "/studies"
        study_path = SwaggerPath(url=studies_url)
        self._build_studies_list_path(study_path)
        self._build_import_study_path(study_path)
        self.swagger.add_path(study_path)

    def _build_copy_study_path(self) -> None:
        url = self.url + "/copy"

        copy_study_path = SwaggerPath(url=url)

        copy_study_path.add_operation(
            SwaggerOperation(verb=SwaggerOperation.OperationVerbs.post)
        )

        dest_parameter = SwaggerParameter(
            name="dest",
            in_=SwaggerParameter.ParametersIn.query,
        )

        copy_study_path.add_parameter(dest_parameter)

        self.swagger.add_path(copy_study_path)

    def _build_study_path(self) -> None:
        study_path = SwaggerPath(url=self.url)

        study_path.add_operation(
            SwaggerOperation(verb=SwaggerOperation.OperationVerbs.get)
        )
        study_path.add_operation(
            SwaggerOperation(verb=SwaggerOperation.OperationVerbs.post)
        )
        study_path.add_operation(
            SwaggerOperation(verb=SwaggerOperation.OperationVerbs.delete)
        )

        self.swagger.add_path(study_path)

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

        self.swagger.add_path(export_path)

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

        self.swagger.add_path(get_file_path)

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
        self._build_path()
        self._build_children()

    def _build_path(self) -> None:
        path = self._get_path()
        self.swagger.add_path(path)

    def _get_path(self) -> SwaggerPath:

        swagger_path = SwaggerPath(url=self.url)

        operation_get = SwaggerOperation(
            verb=SwaggerOperation.OperationVerbs.get
        )
        operation_get.add_tag(self._get_tag())
        swagger_path.add_operation(operation_get)

        return swagger_path

    def _build_children(self) -> None:

        if not self._is_leaf():
            self._build_children_property_based()
            self._build_children_additional_property_based()

    def _is_leaf(self) -> bool:
        return self.jsm.is_swagger_leaf()

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
