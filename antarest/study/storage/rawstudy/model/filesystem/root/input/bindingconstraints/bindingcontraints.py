from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import BindingConstraintFrequency
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency
from antarest.study.storage.rawstudy.model.filesystem.root.input.bindingconstraints.bindingconstraints_ini import (
    BindingConstraintsIni,
)
from antarest.study.storage.variantstudy.business.matrix_constants.binding_constraint.series import (
    default_binding_constraint_daily,
    default_binding_constraint_hourly,
    default_binding_constraint_weekly,
)


class BindingConstraints(FolderNode):
    def build(self) -> TREE:
        default_matrices = {
            BindingConstraintFrequency.HOURLY: default_binding_constraint_hourly,
            BindingConstraintFrequency.DAILY: default_binding_constraint_daily,
            BindingConstraintFrequency.WEEKLY: default_binding_constraint_weekly,
        }
        children: TREE = {
            binding.id: InputSeriesMatrix(
                self.context,
                self.config.next_file(f"{binding.id}.txt"),
                freq=MatrixFrequency(binding.time_step),
                nb_columns=3,
                default_empty=default_matrices[binding.time_step],
            )
            for binding in self.config.bindings
        }

        children["bindingconstraints"] = BindingConstraintsIni(
            self.context, self.config.next_file("bindingconstraints.ini")
        )

        return children
