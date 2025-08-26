from enum import Enum
from typing import List

from pydantic import ConfigDict
from pydantic.alias_generators import to_camel

from antarest.core.serde import AntaresBaseModel


class DistrictUpdateDTO(AntaresBaseModel):
    #: Indicates whether this district is used in the output (usually all
    #: districts are visible, but the user can decide to hide some of them).
    output: bool
    #: User-defined comments.
    comments: str = ""
    #: List of areas that will be grouped in the district.
    areas: List[str]


class DistrictCreationDTO(DistrictUpdateDTO):
    #: Name of the district (this name is also used as a unique identifier).
    name: str


class DistrictInfoDTO(DistrictCreationDTO):
    #: District identifier (based on the district name)
    id: str


class DistrictBaseFilter(Enum):
    add_all = "add-all"
    remove_all = "remove-all"


# classe DistrictCreate


class District(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel, extra="forbid", populate_by_name=True)

    #: District identifier (based on the district name)
    id: str
    #: Indicates whether this district is used in the output (usually all
    #: districts are visible, but the user can decide to hide some of them).
    output: bool
    #: User-defined comments.
    comments: str = ""
    #: List of areas that will be grouped in the district.
    areas: List[str]
    #: Name of the district (this name is also used as a unique identifier).
    name: str
