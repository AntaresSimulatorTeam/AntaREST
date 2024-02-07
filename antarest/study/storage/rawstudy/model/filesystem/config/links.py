"""
Object model used to read and update link configuration.
"""
import typing as t

from pydantic import validator, Field, root_validator

from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.storage.rawstudy.model.filesystem.config.field_validators import (
    validate_filtering,
    validate_colors,
    validate_color_rgb,
)
from antarest.study.storage.rawstudy.model.filesystem.config.ini_properties import IniProperties


# noinspection SpellCheckingInspection
class AssetType(EnumIgnoreCase):
    """
    Enum representing the type of asset for a link between two areas.

    Attributes:
        AC: Represents an Alternating Current link. This is the most common type of electricity transmission.
        DC: Represents a Direct Current link. This is typically used for long-distance transmission.
        GAZ: Represents a gas link. This is used when the link is related to gas transmission.
        VIRT: Represents a virtual link. This is used when the link doesn't physically exist
            but is used for modeling purposes.
        OTHER: Represents any other type of link that doesn't fall into the above categories.
    """

    AC = "ac"
    DC = "dc"
    GAZ = "gaz"
    VIRT = "virt"
    OTHER = "other"


class TransmissionCapacity(EnumIgnoreCase):
    """
    Enum representing the transmission capacity of a link.

    Attributes:
        INFINITE: Represents a link with infinite transmission capacity.
            This means there are no limits on the amount of electricity that can be transmitted.
        IGNORE: Represents a link where the transmission capacity is ignored.
            This means the capacity is not considered during simulations.
        ENABLED: Represents a link with a specific transmission capacity.
            This means the capacity is considered in the model and has a certain limit.
    """

    INFINITE = "infinite"
    IGNORE = "ignore"
    ENABLED = "enabled"


class LinkProperties(IniProperties):
    """
    Configuration read from a section in the `input/links/<area1>/properties.ini` file.

    Usage:

    >>> from antarest.study.storage.rawstudy.model.filesystem.config.links import LinkProperties
    >>> from pprint import pprint

    Create and validate a new `LinkProperties` object from a dictionary read from a configuration file.

    >>> obj = {
    ...     "hurdles-cost": "false",
    ...     "loop-flow": "false",
    ...     "use-phase-shifter": "false",
    ...     "transmission-capacities": "infinite",
    ...     "asset-type": "ac",
    ...     "link-style": "plain",
    ...     "link-width": "1",
    ...     "colorr": "80",
    ...     "colorg": "192",
    ...     "colorb": "255",
    ...     "display-comments": "true",
    ...     "filter-synthesis": "hourly, daily, weekly, monthly, annual",
    ...     "filter-year-by-year": "hourly, daily, weekly, monthly, annual",
    ... }

    >>> opt = LinkProperties.parse_obj(obj)

    >>> pprint(opt.dict(by_alias=True), width=80)
    {'asset-type': <AssetType.AC: 'ac'>,
     'colorRgb': (80, 192, 255),
     'display-comments': True,
     'filter-synthesis': 'hourly, daily, weekly, monthly, annual',
     'filter-year-by-year': 'hourly, daily, weekly, monthly, annual',
     'hurdles-cost': False,
     'link-style': 'plain',
     'link-width': 1,
     'loop-flow': False,
     'transmission-capacities': <TransmissionCapacity.INFINITE: 'infinite'>,
     'use-phase-shifter': False}
    """

    hurdles_cost: bool = Field(default=False, alias="hurdles-cost")
    loop_flow: bool = Field(default=False, alias="loop-flow")
    use_phase_shifter: bool = Field(default=False, alias="use-phase-shifter")
    transmission_capacities: TransmissionCapacity = Field(
        default=TransmissionCapacity.ENABLED, alias="transmission-capacities"
    )
    asset_type: AssetType = Field(default=AssetType.AC, alias="asset-type")
    link_style: str = Field(default="plain", alias="link-style")
    link_width: int = Field(default=1, alias="link-width")
    display_comments: bool = Field(default=True, alias="display-comments")
    filter_synthesis: str = Field(default="hourly, daily, weekly, monthly, annual", alias="filter-synthesis")
    filter_year_by_year: str = Field(default="hourly, daily, weekly, monthly, annual", alias="filter-year-by-year")
    color_rgb: t.Tuple[int, int, int] = Field(
        (112, 112, 112),
        alias="colorRgb",
        description="color of the link in the map",
    )

    _validate_filtering = validator(
        "filter_synthesis",
        "filter_year_by_year",
        pre=True,
        allow_reuse=True,
    )(validate_filtering)

    _validate_color_rgb = validator("color_rgb", pre=True, allow_reuse=True)(validate_color_rgb)

    @root_validator(pre=True)
    def _validate_colors(cls, values: t.MutableMapping[str, t.Any]) -> t.Mapping[str, t.Any]:
        return validate_colors(values)

    # noinspection SpellCheckingInspection
    def to_config(self) -> t.Mapping[str, t.Any]:
        """
        Convert the object to a dictionary for writing to a configuration file.
        """
        obj = dict(super().to_config())
        color_rgb = obj.pop("color_rgb", (112, 112, 112))
        return {
            "colorr": color_rgb[0],
            "colorg": color_rgb[1],
            "colorb": color_rgb[2],
            **obj,
        }
