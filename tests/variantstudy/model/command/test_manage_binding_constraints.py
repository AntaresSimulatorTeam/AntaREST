from antarest.matrixstore.service import MatrixService
from antarest.study.storage.rawstudy.io.reader import IniReader
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.matrix_constants_generator import (
    GeneratorMatrixConstants,
)
from antarest.study.storage.variantstudy.model.command.common import (
    BindingConstraintOperator,
    TimeStep,
)
from antarest.study.storage.variantstudy.model.command.create_area import (
    CreateArea,
)
from antarest.study.storage.variantstudy.model.command.create_binding_constraint import (
    CreateBindingConstraint,
)
from antarest.study.storage.variantstudy.model.command.create_cluster import (
    CreateCluster,
)
from antarest.study.storage.variantstudy.model.command.create_link import (
    CreateLink,
)
from antarest.study.storage.variantstudy.model.command.remove_binding_constraint import (
    RemoveBindingConstraint,
)
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)


def test_manage_district(
    empty_study: FileStudy, matrix_service: MatrixService
):
    command_context = CommandContext(
        generator_matrix_constants=GeneratorMatrixConstants(
            matrix_service=matrix_service
        ),
        matrix_service=matrix_service,
    )
    study_path = empty_study.config.study_path

    area1 = "area1"
    area2 = "area2"
    cluster = "cluster"
    CreateArea.parse_obj(
        {
            "area_name": area1,
            "metadata": {},
            "command_context": command_context,
        }
    ).apply(empty_study)
    CreateArea.parse_obj(
        {
            "area_name": area2,
            "metadata": {},
            "command_context": command_context,
        }
    ).apply(empty_study)
    CreateLink.parse_obj(
        {
            "area1": area1,
            "area2": area2,
            "parameters": {},
            "command_context": command_context,
        }
    ).apply(empty_study)
    CreateCluster.parse_obj(
        {
            "area_id": area1,
            "cluster_name": cluster,
            "parameters": {},
            "command_context": command_context,
        }
    ).apply(empty_study)

    bind1_cmd = CreateBindingConstraint(
        name="BD 1",
        time_step=TimeStep.HOURLY,
        operator=BindingConstraintOperator.LESS,
        coeffs={"area1%area2": [800, 30]},
        comments="Hello",
        command_context=command_context,
    )
    res = bind1_cmd.apply(empty_study)
    assert res.status

    bind2_cmd = CreateBindingConstraint(
        name="BD 2",
        enabled=False,
        time_step=TimeStep.DAILY,
        operator=BindingConstraintOperator.BOTH,
        coeffs={"area1.cluster": [50]},
        command_context=command_context,
    )
    res2 = bind2_cmd.apply(empty_study)
    assert res2.status

    assert (
        study_path / "input" / "bindingconstraints" / "bd 1.txt.link"
    ).exists()
    assert (
        study_path / "input" / "bindingconstraints" / "bd 2.txt.link"
    ).exists()
    bd_config = IniReader().read(
        study_path / "input" / "bindingconstraints" / "bindingconstraints.ini"
    )
    assert bd_config.get("0") == {
        "name": "BD 1",
        "id": "bd 1",
        "enabled": True,
        "comments": "Hello",
        "area1%area2": "800.0%30",
        "operator": "less",
        "type": "hourly",
    }
    assert bd_config.get("1") == {
        "name": "BD 2",
        "id": "bd 2",
        "enabled": False,
        "area1.cluster": 50.0,
        "operator": "both",
        "type": "daily",
    }

    remove_bind = RemoveBindingConstraint(
        id="bd 1", command_context=command_context
    )
    res3 = remove_bind.apply(empty_study)
    assert res3.status
    assert not (
        study_path / "input" / "bindingconstraints" / "bd 1.txt.link"
    ).exists()
    bd_config = IniReader().read(
        study_path / "input" / "bindingconstraints" / "bindingconstraints.ini"
    )
    assert len(bd_config) == 1
    assert bd_config.get("0") == {
        "name": "BD 2",
        "id": "bd 2",
        "enabled": False,
        "area1.cluster": 50.0,
        "operator": "both",
        "type": "daily",
    }
