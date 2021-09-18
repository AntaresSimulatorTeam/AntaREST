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
from antarest.study.storage.variantstudy.model.command.remove_link import (
    RemoveLink,
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
        command_context: CommandContext,
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

        create_area_command: ICommand = CreateArea.parse_obj(
            {
                "area_name": area_name,
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


def test_match(command_context: CommandContext):
    base = RemoveArea(id="foo", command_context=command_context)
    other_match = RemoveArea(id="foo", command_context=command_context)
    other_not_match = RemoveArea(id="bar", command_context=command_context)
    other_other = RemoveLink(
        area1="id", area2="id2", command_context=command_context
    )
    assert base.match(other_match)
    assert not base.match(other_not_match)
    assert not base.match(other_other)
    assert base.match_signature() == "remove_area%foo"
    assert base.get_inner_matrices() == []
