from checksumdir import dirhash

from antarest.matrixstore.service import MatrixService
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.matrix_constants_generator import (
    GeneratorMatrixConstants,
)
from antarest.study.storage.variantstudy.model.command.create_area import (
    CreateArea,
)
from antarest.study.storage.variantstudy.model.command.create_cluster import (
    CreateCluster,
)
from antarest.study.storage.variantstudy.model.command.remove_cluster import (
    RemoveCluster,
)
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)


class TestRemoveCluster:
    def test_validation(self, empty_study: FileStudy):
        pass

    def test_apply(
        self, empty_study: FileStudy, matrix_service: MatrixService
    ):

        command_context = CommandContext(
            generator_matrix_constants=GeneratorMatrixConstants(
                matrix_service=matrix_service
            )
        )
        area_name = "Area_name"
        cluster_name = "Cluster_name"

        CreateArea.parse_obj(
            {
                "area_name": area_name,
                "metadata": {},
                "command_context": command_context,
            }
        ).apply(empty_study)

        hash_before_cluster = dirhash(empty_study.config.study_path, "md5")

        command_context = CommandContext(matrix_service=matrix_service)

        CreateCluster(
            area_name=area_name,
            cluster_name=cluster_name,
            parameters={
                "group": "group",
                "unitcount": "unitcount",
                "nominalcapacity": "nominalcapacity",
                "marginal-cost": "marginal-cost",
                "market-bid-cost": "market-bid-cost",
            },
            command_context=command_context,
            prepro=[[0]],
            modulation=[[0]],
        ).apply(empty_study)

        output = RemoveCluster(
            area_name=area_name,
            cluster_name=cluster_name,
        ).apply(empty_study)

        assert output.status
        assert (
            dirhash(empty_study.config.study_path, "md5")
            == hash_before_cluster
        )

        output = RemoveCluster(
            area_name="non_existent_area",
            cluster_name=cluster_name,
        ).apply(empty_study)
        assert not output.status

        output = RemoveCluster(
            area_name=cluster_name,
            cluster_name="non_existent_cluster",
        ).apply(empty_study)
        assert not output.status
