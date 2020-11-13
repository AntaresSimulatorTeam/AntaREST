from typing import cast, List, Optional

from api_iso_antares.custom_types import JSON, SUB_JSON


class JsonSchema:
    def __init__(self, data: JSON) -> None:
        self.data = data

    def get_properties(self) -> List[str]:

        return [
            key for key in self.data["properties"].keys() if not (key == "$id")
        ]

    def has_properties(self) -> bool:
        return "properties" in self.data

    def get_child(self, key: Optional[str] = None) -> "JsonSchema":
        data: JSON
        if (
            self.has_additional_properties()
            and key not in self.get_properties()
        ):
            return self.get_additional_properties()
        else:
            if key is None:
                data = self.data["items"]
            else:
                data = self.data["properties"][key]
        return JsonSchema(data)

    def get_additional_properties(self) -> "JsonSchema":
        data = self.data["additionalProperties"]
        return JsonSchema(data)

    def get_additional_property_name(self) -> str:
        name = self.get_metadata_element("additional_property_name")
        return cast(str, name)

    def has_additional_properties(self) -> bool:
        return "additionalProperties" in self.data

    def has_defined_additional_properties(self) -> bool:
        has_defined_additional_properties = (
            self.has_additional_properties()
            and isinstance(self.data["additionalProperties"], dict)
        )
        return has_defined_additional_properties

    def get_metadata(self) -> Optional[JSON]:
        return self.data.get("rte-metadata", None)

    def get_metadata_element(self, key: str) -> SUB_JSON:
        metadata = self.get_metadata()
        element: SUB_JSON = None
        if metadata is not None:
            element = metadata.get(key, None)
        return element

    def get_filename(self) -> Optional[str]:
        return cast(str, self.get_metadata_element("filename"))

    def get_filename_extension(self) -> Optional[str]:
        return cast(str, self.get_metadata_element("file_extension"))

    def get_strategy(self) -> Optional[str]:
        return cast(Optional[str], self.get_metadata_element("strategy"))

    def is_file(self) -> bool:
        filename = self.get_filename()
        extension = self.get_filename_extension()
        return (filename is not None) or (extension is not None)

    def get_type(self) -> str:
        return cast(str, self.data["type"])

    def is_array(self) -> bool:
        return self.get_type() == "array"

    def is_object(self) -> bool:
        return self.get_type() == "object"

    def is_value(self) -> bool:
        return self.get_type() in ["string", "number", "boolean", "integer"]
