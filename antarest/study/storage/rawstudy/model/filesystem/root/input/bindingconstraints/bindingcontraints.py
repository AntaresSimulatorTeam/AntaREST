from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import BindingConstraintFrequency
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency
from antarest.study.storage.rawstudy.model.filesystem.root.input.bindingconstraints.bindingconstraints_ini import (
    BindingConstraintsIni,
)
from antarest.study.storage.variantstudy.business.matrix_constants.binding_constraint.series import (
    default_bc_hourly,
    default_bc_weekly_daily,
)


class BindingConstraints(FolderNode):
    """
    Handle the binding constraints folder which contains the binding constraints
    configuration and matrices.
    """

    def build(self) -> TREE:
        default_matrices = {
            BindingConstraintFrequency.HOURLY: default_bc_hourly,
            BindingConstraintFrequency.DAILY: default_bc_weekly_daily,
            BindingConstraintFrequency.WEEKLY: default_bc_weekly_daily,
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

        # noinspection SpellCheckingInspection
        children["bindingconstraints"] = BindingConstraintsIni(
            self.context, self.config.next_file("bindingconstraints.ini")
        )

        return children
