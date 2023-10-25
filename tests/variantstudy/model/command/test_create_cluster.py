import configparser
import re

import numpy as np
import pytest
from pydantic import ValidationError

from antarest.study.storage.rawstudy.model.filesystem.config.model import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.command_reverter import CommandReverter
from antarest.study.storage.variantstudy.model.command.common import CommandName
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_cluster import CreateCluster
from antarest.study.storage.variantstudy.model.command.remove_cluster import RemoveCluster
from antarest.study.storage.variantstudy.model.command.replace_matrix import ReplaceMatrix
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class TestCreateCluster:
    def test_init(self, command_context: CommandContext):
        prepro = np.random.rand(365, 6).tolist()
        modulation = np.random.rand(8760, 4).tolist()
        cl = CreateCluster(
            area_id="foo",
            cluster_name="Cluster1",
            parameters={"group": "Nuclear", "unitcount": 2, "nominalcapacity": 2400},
            command_context=command_context,
            prepro=prepro,
            modulation=modulation,
        )

        # Check the command metadata
        assert cl.command_name == CommandName.CREATE_THERMAL_CLUSTER
        assert cl.version == 1
        assert cl.command_context is command_context

        # Check the command data
        prepro_id = command_context.matrix_service.create(prepro)
        modulation_id = command_context.matrix_service.create(modulation)
        assert cl.area_id == "foo"
        assert cl.cluster_name == "Cluster1"
        assert cl.parameters == {"group": "Nuclear", "nominalcapacity": "2400", "unitcount": "2"}
        assert cl.prepro == f"matrix://{prepro_id}"
        assert cl.modulation == f"matrix://{modulation_id}"

    def test_validate_cluster_name(self, command_context: CommandContext):
        with pytest.raises(ValidationError, match="cluster_name"):
            CreateCluster(area_id="fr", cluster_name="%", command_context=command_context, parameters={})

    def test_validate_prepro(self, command_context: CommandContext):
        cl = CreateCluster(area_id="fr", cluster_name="C1", command_context=command_context, parameters={})
        assert cl.prepro == command_context.generator_matrix_constants.get_thermal_prepro_data()

    def test_validate_modulation(self, command_context: CommandContext):
        cl = CreateCluster(area_id="fr", cluster_name="C1", command_context=command_context, parameters={})
        assert cl.modulation == command_context.generator_matrix_constants.get_thermal_prepro_modulation()

    def test_apply(self, empty_study: FileStudy, command_context: CommandContext):
        study_path = empty_study.config.study_path
        area_name = "DE"
        area_id = transform_name_to_id(area_name, lower=True)
        cluster_name = "Cluster-1"
        cluster_id = transform_name_to_id(cluster_name, lower=True)

        CreateArea(area_name=area_name, command_context=command_context).apply(empty_study)

        parameters = {
            "group": "Other",
            "unitcount": "1",
            "nominalcapacity": "1000000",
            "marginal-cost": "30",
            "market-bid-cost": "30",
        }

        prepro = np.random.rand(365, 6).tolist()
        modulation = np.random.rand(8760, 4).tolist()
        command = CreateCluster(
            area_id=area_id,
            cluster_name=cluster_name,
            parameters=parameters,
            prepro=prepro,
            modulation=modulation,
            command_context=command_context,
        )

        output = command.apply(empty_study)
        assert output.status is True
        assert re.match(
            r"Thermal cluster 'cluster-1' added to area 'de'",
            output.message,
            flags=re.IGNORECASE,
        )

        clusters = configparser.ConfigParser()
        clusters.read(study_path / "input" / "thermal" / "clusters" / area_id / "list.ini")
        assert str(clusters[cluster_name]["name"]) == cluster_name
        assert str(clusters[cluster_name]["group"]) == parameters["group"]
        assert int(clusters[cluster_name]["unitcount"]) == int(parameters["unitcount"])
        assert float(clusters[cluster_name]["nominalcapacity"]) == float(parameters["nominalcapacity"])
        assert float(clusters[cluster_name]["marginal-cost"]) == float(parameters["marginal-cost"])
        assert float(clusters[cluster_name]["market-bid-cost"]) == float(parameters["market-bid-cost"])

        assert (study_path / "input" / "thermal" / "prepro" / area_id / cluster_id / "data.txt.link").exists()
        assert (study_path / "input" / "thermal" / "prepro" / area_id / cluster_id / "modulation.txt.link").exists()

        output = CreateCluster(
            area_id=area_id,
            cluster_name=cluster_name,
            parameters=parameters,
            prepro=prepro,
            modulation=modulation,
            command_context=command_context,
        ).apply(empty_study)
        assert output.status is False
        assert re.match(
            r"Thermal cluster 'cluster-1' already exists in the area 'de'",
            output.message,
            flags=re.IGNORECASE,
        )

        output = CreateCluster(
            area_id="non_existent_area",
            cluster_name=cluster_name,
            parameters=parameters,
            prepro=prepro,
            modulation=modulation,
            command_context=command_context,
        ).apply(empty_study)
        assert output.status is False
        assert re.match(
            r"Area 'non_existent_area' does not exist",
            output.message,
            flags=re.IGNORECASE,
        )

    def test_to_dto(self, command_context: CommandContext):
        prepro = np.random.rand(365, 6).tolist()
        modulation = np.random.rand(8760, 4).tolist()
        command = CreateCluster(
            area_id="foo",
            cluster_name="Cluster1",
            parameters={"group": "Nuclear", "unitcount": 2, "nominalcapacity": 2400},
            command_context=command_context,
            prepro=prepro,
            modulation=modulation,
        )
        prepro_id = command_context.matrix_service.create(prepro)
        modulation_id = command_context.matrix_service.create(modulation)
        dto = command.to_dto()
        assert dto.dict() == {
            "action": "create_cluster",
            "args": {
                "area_id": "foo",
                "cluster_name": "Cluster1",
                "parameters": {"group": "Nuclear", "nominalcapacity": "2400", "unitcount": "2"},
                "prepro": prepro_id,
                "modulation": modulation_id,
            },
            "id": None,
            "version": 1,
        }


def test_match(command_context: CommandContext):
    prepro = np.random.rand(365, 6).tolist()
    modulation = np.random.rand(8760, 4).tolist()
    base = CreateCluster(
        area_id="foo",
        cluster_name="foo",
        parameters={},
        prepro=prepro,
        modulation=modulation,
        command_context=command_context,
    )
    other_match = CreateCluster(
        area_id="foo",
        cluster_name="foo",
        parameters={},
        prepro=prepro,
        modulation=modulation,
        command_context=command_context,
    )
    other_not_match = CreateCluster(
        area_id="foo",
        cluster_name="bar",
        parameters={},
        prepro=prepro,
        modulation=modulation,
        command_context=command_context,
    )
    other_other = RemoveCluster(area_id="id", cluster_id="id", command_context=command_context)
    assert base.match(other_match)
    assert not base.match(other_not_match)
    assert not base.match(other_other)

    assert base.match(other_match, equal=True)
    assert not base.match(other_not_match, equal=True)
    assert not base.match(other_other, equal=True)

    assert base.match_signature() == "create_cluster%foo%foo"

    # check the matrices links
    prepro_id = command_context.matrix_service.create(prepro)
    modulation_id = command_context.matrix_service.create(modulation)
    assert base.get_inner_matrices() == [prepro_id, modulation_id]


def test_revert(command_context: CommandContext):
    base = CreateCluster(
        area_id="foo",
        cluster_name="foo",
        parameters={},
        command_context=command_context,
    )
    assert CommandReverter().revert(base, [], None) == [
        RemoveCluster(
            area_id="foo",
            cluster_id="foo",
            command_context=command_context,
        )
    ]


def test_create_diff(command_context: CommandContext):
    prepro_a = np.random.rand(365, 6).tolist()
    modulation_a = np.random.rand(8760, 4).tolist()
    base = CreateCluster(
        area_id="foo",
        cluster_name="foo",
        parameters={},
        prepro=prepro_a,
        modulation=modulation_a,
        command_context=command_context,
    )

    prepro_b = np.random.rand(365, 6).tolist()
    modulation_b = np.random.rand(8760, 4).tolist()
    other_match = CreateCluster(
        area_id="foo",
        cluster_name="foo",
        parameters={"nominalcapacity": "2400"},
        prepro=prepro_b,
        modulation=modulation_b,
        command_context=command_context,
    )

    assert base.create_diff(other_match) == [
        ReplaceMatrix(
            target=f"input/thermal/prepro/foo/foo/data",
            matrix=prepro_b,
            command_context=command_context,
        ),
        ReplaceMatrix(
            target=f"input/thermal/prepro/foo/foo/modulation",
            matrix=modulation_b,
            command_context=command_context,
        ),
        UpdateConfig(
            target=f"input/thermal/clusters/foo/list/foo",
            data={"nominalcapacity": "2400"},
            command_context=command_context,
        ),
    ]
