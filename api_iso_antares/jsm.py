from typing import cast, List, Optional, Any

from api_iso_antares.custom_types import JSON, SUB_JSON


class JsonSchema:
    def __init__(self, data: JSON) -> None:
        self.data = data

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, dict):
            return self.data == other
        elif isinstance(other, JsonSchema):
            return self.data == other.data
        else:
            return False

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return self.__str__()

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
            data = self.data["properties"][key]
        return JsonSchema(data)

    def get_additional_properties(self) -> "JsonSchema":

        if "additionalProperties" in self.data:
            data = self.data["additionalProperties"]
        elif "patternProperties" in self.data:
            patterns = list(self.data["patternProperties"].values())
            data = patterns[0]
        else:
            raise KeyError("additionalProperties or patternProperties")
        return JsonSchema(data)

    def get_pattern_properties(self) -> Optional[str]:
        pattern = None
        if "patternProperties" in self.data:
            patterns = list(self.data["patternProperties"].keys())
            pattern = patterns[0]
        return pattern

    def get_additional_property_name(self) -> str:
        name = self.get_metadata_element("additional_property_name")
        return cast(str, name)

    def has_additional_properties(self) -> bool:
        return (
            "additionalProperties" in self.data
            or "patternProperties" in self.data
        )

    def has_defined_additional_properties(self) -> bool:

        has_additional_properties = self.has_additional_properties()

        additional_properties = None
        if has_additional_properties:
            additional_properties = self.get_additional_properties()

        return additional_properties is not None

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

    def is_swagger_leaf(self) -> bool:
        return cast(bool, self.get_metadata_element("swagger_stop")) or False

    def is_file(self) -> bool:
        filename = self.get_filename()
        extension = self.get_filename_extension()
        return (filename is not None) or (extension is not None)

    def is_ini_file(self) -> bool:
        name = self.get_filename()
        ext = self.get_filename_extension()
        if name:
            return name.split(".")[-1] in ["ini", "antares", "dat"]
        elif ext:
            return ext in [".ini", ".antares", ".dat"]
        else:
            return False

    def get_type(self) -> str:
        return cast(str, self.data["type"])

    def is_array(self) -> bool:
        return self.get_type() == "array"

    def is_object(self) -> bool:
        return self.get_type() == "object"

    def is_value(self) -> bool:
        return self.get_type() in ["string", "number", "boolean", "integer"]
