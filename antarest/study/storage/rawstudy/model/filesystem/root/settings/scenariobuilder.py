import typing as t

from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode


class ScenarioBuilder(IniFileNode):
    """
    Node representing the `settings/scenariobuilder.dat` file in an Antares study.

    This ".dat" file is a kind of ".ini"" file, where sections are rulesets.
    Each ruleset is a set of rules defined for each kind of generator or link.

    | Label                  | Symbol | Format                                     | Availability |
    |------------------------|:------:|--------------------------------------------|:------------:|
    | load                   |   l    | `l,<area>,<year> = <TS number>`            |              |
    | thermal                |   t    | `t,<area>,<year>,<cluster> = <TS number>`  |              |
    | hydro                  |   h    | `h,<area>,<year> = <TS number>`            |              |
    | wind                   |   w    | `w,<area>,<year> = <TS number>`            |              |
    | solar                  |   s    | `s,<area>,<year> = <TS number>`            |              |
    | NTC (links)            |  ntc   | `ntc,<area1>,<area2>,<year> = <TS number>` |              |
    | renewable              |   r    | `r,<area>,<year>,<cluster> = <TS number>`  |     8.1      |
    | binding-constraints    |   bc   | `bc,<group>,<year> = <TS number>`          |     8.7      |
    | hydro initial levels   |   hl   | `hl,<area>,<year> = <Level>`               |     8.0      |
    | hydro final levels     |  hfl   | `hfl,<area>,<year> = <Level>`              |     9.2      |
    | hydro generation power |  hgp   | `hgp,<area>,<year> = <TS number>`          |     9.1      |

    Legend:

    - `<area>`: The area ID (in lower case).
    - `<area1>`, `<area2>`: The area IDs of the two connected areas (source and target).
    - `<year>`: The year (0-based index) of the time series.
    - `<cluster>`: The ID of the thermal / renewable cluster (in lower case).
    - `<group>`: The ID of the binding constraint group (in lower case).
    - `<TS number>`: The time series number (1-based index of the matrix column).
    - `<Level>`: The level of the hydraulic reservoir (in range 0-1).
    """

    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        self.config = config

        study_version = int(config.version)

        rules: t.Dict[str, t.Union[t.Type[int], t.Type[float]]] = {}

        # Add area-specific rules
        for area in self.config.areas:
            # load, hydro, wind, solar generators
            symbols: t.Tuple[str, ...] = ("l", "h", "w", "s")
            if study_version >= 920:
                symbols += ("hgp",)  # Hydro generation power
            rules.update({f"{symbol},{area},0": int for symbol in symbols})

            # Hydro levels
            if study_version >= 800:
                rules[f"hl,{area},0"] = float
            if study_version >= 920:
                rules[f"hfl,{area},0"] = float

            # thermal clusters
            cluster_ids = (_id.lower() for _id in self.config.get_thermal_ids(area))
            rules.update({f"t,{area},0,{cluster_id}": int for cluster_id in cluster_ids})

            if study_version >= 810:
                # renewable clusters
                cluster_ids = (_id.lower() for _id in self.config.get_renewable_ids(area))
                rules.update({f"r,{area},0,{cluster_id}": int for cluster_id in cluster_ids})

            # NTC (links)
            area2_ids = config.get_links(area)
            rules.update({f"ntc,{area},{area2},0": int for area2 in area2_ids})

            # Binding constraints
            if study_version >= 870:
                bc_groups = config.get_binding_constraint_groups()
                rules.update({f"bc,{grp},0": int for grp in bc_groups})

        super().__init__(context=context, config=config, types={"Default Ruleset": rules})
