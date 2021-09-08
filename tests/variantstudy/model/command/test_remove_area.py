from checksumdir import dirhash

from antarest.matrixstore.service import MatrixService
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    transform_name_to_id,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.matrix_constants_generator import (
    GeneratorMatrixConstants,
)
from antarest.study.storage.variantstudy.model.command.create_area import (
    CreateArea,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.remove_area import (
    RemoveArea,
)
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)


class TestRemoveArea:
    def test_validation(self, empty_study: FileStudy):
        pass

    def test_apply(
        self,
        empty_study: FileStudy,
        matrix_service: MatrixService,
    ):
        area_name = "Area"
        empty_study.tree.save(
            {
                "input": {
                    "thermal": {
                        "areas": {
                            "unserverdenergycost": {},
                            "spilledenergycost": {},
                        }
                    },
                    "hydro": {
                        "hydro": {
                            "inter-daily-breakdown": {},
                            "intra-daily-modulation": {},
                            "inter-monthly-breakdown": {},
                            "initialize reservoir date": {},
                            "leeway low": {},
                            "leeway up": {},
                            "pumping efficiency": {},
                        }
                    },
                }
            }
        )

        empty_study_hash = dirhash(empty_study.config.study_path, "md5")
        command_context = CommandContext(
            generator_matrix_constants=GeneratorMatrixConstants(
                matrix_service=matrix_service
            )
        )

        create_area_command: ICommand = CreateArea.parse_obj(
            {
                "area_name": area_name,
                "metadata": {},
                "command_context": command_context,
            }
        )
        create_area_command.apply(study_data=empty_study)

        remove_area_commande: ICommand = RemoveArea.parse_obj(
            {
                "id": transform_name_to_id(area_name),
                "command_context": command_context,
            }
        )
        output = remove_area_commande.apply(study_data=empty_study)
        assert output.status

        assert (
            dirhash(empty_study.config.study_path, "md5") == empty_study_hash
        )
