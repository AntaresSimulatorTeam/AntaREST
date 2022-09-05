from antarest.study.storage.rawstudy.model.filesystem.bucket_node import (
    BucketNode,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.simulation import (
    OutputSimulation,
)


class Output(FolderNode):
    def build(self) -> TREE:
        children: TREE = {
            str(s.get_file()): OutputSimulation(
                self.context,
                self.config.next_file(s.get_file(), is_output=True),
                s,
            )
            for i, s in self.config.outputs.items()
        }

        children["logs"] = BucketNode(
            self.context, self.config.next_file("logs")
        )
        return children
