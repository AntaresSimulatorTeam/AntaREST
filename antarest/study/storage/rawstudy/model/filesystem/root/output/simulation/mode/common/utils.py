from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.common.areas import (
    OutputSimulationAreas,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.common.binding_const import (
    OutputSimulationBindingConstraintItem,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.common.links import (
    OutputSimulationLinks,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcall.grid import (
    OutputSimulationModeMcAllGrid,
)

OUTPUT_MAPPING = {
    "areas": OutputSimulationAreas,
    "grid": OutputSimulationModeMcAllGrid,
    "links": OutputSimulationLinks,
    "binding_constraints": OutputSimulationBindingConstraintItem,
}
