import typing as t

from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE, INode
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix


class AreaMatrixList(FolderNode):
    """
    Represents a folder structure, which contains a list of matrix files.

    Each matrix file has a specific naming convention: "{prefix}{area}.txt",
    where ``prefix`` is a user-defined file name prefix applied to all files,
    and ``area`` is an identifier for a specific area.

    The class provides read and write access to each matrix file
    using an :class:`InputSeriesMatrix` object.

    Parameters:

    - ``context``: The context server associated with the folder.
    - ``config``: The file study tree configuration for the folder.
    - ``prefix`` (optional): The file name prefix used for all files in the folder.
    - ``matrix_class`` (optional): The class representing the matrix objects.
    - ``additional_matrix_params`` (optional): Additional parameters to be passed to the
      matrix class during instantiation.

    Example of tree structure:

    .. code-block:: text

       input/load/series/
       ├── load_flex.txt
       ├── load_peak.txt
       ├── load_store_in.txt
       └── load_store_out.txt
    """

    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        *,
        prefix: str = "",
        matrix_class: t.Callable[..., INode[t.Any, t.Any, t.Any]] = InputSeriesMatrix,
        additional_matrix_params: t.Optional[t.Dict[str, t.Any]] = None,
    ):
        super().__init__(context, config)
        self.prefix = prefix
        self.matrix_class = matrix_class
        self.additional_matrix_params = additional_matrix_params or {}

    def build(self) -> TREE:
        """
        Builds the folder structure and creates child nodes representing each matrix file.

        Returns:
            A dictionary of child nodes, where the key is the matrix file name
            and the value is the corresponding :class:`InputSeriesMatrix` node.
        """
        children: TREE = {
            f"{self.prefix}{area}": self.matrix_class(
                self.context,
                self.config.next_file(f"{self.prefix}{area}.txt"),
                **self.additional_matrix_params,
            )
            for area in self.config.area_names()
        }
        return children


class HydroMatrixList(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        area: str,
        matrix_class: t.Callable[[ContextServer, FileStudyTreeConfig], INode[t.Any, t.Any, t.Any]],
    ):
        super().__init__(context, config)
        self.area = area
        self.matrix_class = matrix_class

    def build(self) -> TREE:
        children: TREE = {
            "ror": self.matrix_class(self.context, self.config.next_file("ror.txt")),
            "storage": self.matrix_class(self.context, self.config.next_file("storage.txt")),
        }
        return children


class BindingConstraintMatrixList(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        matrix_class: t.Callable[[ContextServer, FileStudyTreeConfig], INode[t.Any, t.Any, t.Any]],
    ):
        super().__init__(context, config)
        self.matrix_class = matrix_class

    def build(self) -> TREE:
        """Builds the folder structure and creates child nodes representing each matrix file."""
        return {
            file.stem: self.matrix_class(self.context, self.config.next_file(file.name))
            for file in self.config.path.glob("*.txt")
        }


class ThermalMatrixList(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        area: str,
        matrix_class: t.Callable[[ContextServer, FileStudyTreeConfig], INode[t.Any, t.Any, t.Any]],
    ):
        super().__init__(context, config)
        self.area = area
        self.matrix_class = matrix_class

    def build(self) -> TREE:
        # Note that cluster IDs are case-insensitive, but series IDs are in lower case.
        # For instance, if your cluster ID is "Base", then the series ID will be "base".
        series_ids = map(str.lower, self.config.get_thermal_ids(self.area))
        children: TREE = {
            series_id: self.matrix_class(self.context, self.config.next_file(f"{series_id}.txt"))
            for series_id in series_ids
        }
        return children


class AreaMultipleMatrixList(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        klass: t.Callable[
            [
                ContextServer,
                FileStudyTreeConfig,
                str,
                t.Callable[
                    [ContextServer, FileStudyTreeConfig],
                    INode[t.Any, t.Any, t.Any],
                ],
            ],
            INode[t.Any, t.Any, t.Any],
        ],
        matrix_class: t.Callable[[ContextServer, FileStudyTreeConfig], INode[t.Any, t.Any, t.Any]],
    ):
        super().__init__(context, config)
        self.klass = klass
        self.matrix_class = matrix_class

    def build(self) -> TREE:
        children: TREE = {
            area: self.klass(
                self.context,
                self.config.next_file(area),
                area,
                self.matrix_class,
            )
            for area in self.config.area_names()
        }
        return children
