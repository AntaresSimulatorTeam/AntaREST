import pytest
from checksumdir import dirhash

from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import (
    BindingConstraintFrequency,
    BindingConstraintOperator,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_binding_constraint import CreateBindingConstraint
from antarest.study.storage.variantstudy.model.command.create_cluster import CreateCluster
from antarest.study.storage.variantstudy.model.command.create_district import CreateDistrict, DistrictBaseFilter
from antarest.study.storage.variantstudy.model.command.create_link import CreateLink
from antarest.study.storage.variantstudy.model.command.create_renewables_cluster import CreateRenewablesCluster
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.remove_area import RemoveArea
from antarest.study.storage.variantstudy.model.command.remove_district import RemoveDistrict
from antarest.study.storage.variantstudy.model.command.remove_link import RemoveLink
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
from antarest.study.storage.variantstudy.model.command.update_scenario_builder import UpdateScenarioBuilder
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.variantstudy.model.command.helpers import reset_line_separator


class TestRemoveArea:
    @pytest.mark.parametrize("empty_study", ["empty_study_810.zip", "empty_study_840.zip"], indirect=True)
    def test_apply(self, empty_study: FileStudy, command_context: CommandContext):
        # noinspection SpellCheckingInspection
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

        area_name = "Area"
        area_id = transform_name_to_id(area_name)
        create_area_command: ICommand = CreateArea(area_name=area_name, command_context=command_context)
        output = create_area_command.apply(study_data=empty_study)
        assert output.status, output.message

        create_district_command = CreateDistrict(
            name="foo",
            base_filter=DistrictBaseFilter.add_all,
            filter_items=[area_id],
            command_context=command_context,
        )
        output = create_district_command.apply(study_data=empty_study)
        assert output.status, output.message

        # Change the MC years to 5 to test the scenario builder data
        empty_study.tree.save(5, ["settings", "generaldata", "general", "nbyears"])

        if empty_study.config.version >= 810:
            # Parameter 'renewable-generation-modelling' must be set to 'clusters' instead of 'aggregated'
            update_config = UpdateConfig(
                target="settings/generaldata/other preferences",
                data={"renewable-generation-modelling": "clusters"},
                command_context=command_context,
            )
            output = update_config.apply(study_data=empty_study)
            assert output.status, output.message

        ########################################################################################

        # Line ending of the `settings/scenariobuilder.dat` must be reset before checksum
        reset_line_separator(empty_study.config.study_path.joinpath("settings/scenariobuilder.dat"))
        hash_before_removal = dirhash(empty_study.config.study_path, "md5")

        empty_study_cfg = empty_study.tree.get(depth=999)
        if empty_study.config.version >= 830:
            empty_study_cfg["input"]["areas"][area_id]["adequacy_patch"] = {
                "adequacy-patch": {"adequacy-patch-mode": "outside"}
            }
            empty_study_cfg["input"]["links"][area_id]["capacities"] = {}

        area_name2 = "Area2"
        area_id2 = transform_name_to_id(area_name2)

        create_area_command: ICommand = CreateArea(area_name=area_name2, command_context=command_context)
        output = create_area_command.apply(study_data=empty_study)
        assert output.status, output.message

        create_link_command: ICommand = CreateLink(
            area1=area_id,
            area2=area_id2,
            parameters={},
            command_context=command_context,
            series=[[0]],
        )
        output = create_link_command.apply(study_data=empty_study)
        assert output.status, output.message

        thermal_name = "cluster"
        thermal_id = transform_name_to_id(thermal_name)
        output = CreateCluster(
            area_id=area_id2,
            cluster_name=thermal_name,
            parameters={
                "group": "Other",
                "unitcount": "1",
                "nominalcapacity": "1000000",
                "marginal-cost": "30",
                "market-bid-cost": "30",
            },
            prepro=[[0]],
            modulation=[[0]],
            command_context=command_context,
        ).apply(study_data=empty_study)
        assert output.status, output.message

        renewable_id = None
        if empty_study.config.version >= 810:
            renewable_name = "Renewable"
            renewable_id = transform_name_to_id(renewable_name)
            output = CreateRenewablesCluster(
                area_id=area_id2,
                cluster_name=renewable_name,
                parameters={
                    "enabled": "true",
                    "group": "Solar Rooftop",
                    "unitcount": "10",
                    "nominalcapacity": "12000",
                    "ts-interpretation": "power-generation",
                },
                command_context=command_context,
            ).apply(study_data=empty_study)
            assert output.status, output.message

        bind1_cmd = CreateBindingConstraint(
            name="BD 2",
            time_step=BindingConstraintFrequency.HOURLY,
            operator=BindingConstraintOperator.LESS,
            coeffs={
                f"{area_id}%{area_id2}": [400, 30],
                f"{area_id2}.cluster": [400, 30],
            },
            comments="Hello",
            command_context=command_context,
        )
        output = bind1_cmd.apply(study_data=empty_study)
        assert output.status, output.message

        remove_district_command = RemoveDistrict(
            id="foo",
            command_context=command_context,
        )
        output = remove_district_command.apply(study_data=empty_study)
        assert output.status, output.message

        create_district_command = CreateDistrict(
            name="foo",
            base_filter=DistrictBaseFilter.add_all,
            filter_items=[area_id, area_id2],
            command_context=command_context,
        )
        output = create_district_command.apply(study_data=empty_study)
        assert output.status, output.message

        # Add scenario builder data
        default_ruleset = {
            f"l,{area_id2},0": 1,
            f"h,{area_id2},0": 1,
            f"w,{area_id2},0": 1,
            f"s,{area_id2},0": 1,
            f"ntc,{area_id},{area_id2},0": 1,
            f"t,{area_id2},0,{thermal_id.lower()}": 1,
        }
        if empty_study.config.version >= 800:
            default_ruleset[f"hl,{area_id2},0"] = 1
        if empty_study.config.version >= 810:
            default_ruleset[f"r,{area_id2},0,{renewable_id.lower()}"] = 1
        if empty_study.config.version >= 870:
            default_ruleset[f"bc,bd 2,0"] = 1
        if empty_study.config.version >= 920:
            default_ruleset[f"hfl,{area_id2},0"] = 1
        if empty_study.config.version >= 910:
            default_ruleset[f"hgp,{area_id2},0"] = 1

        output = UpdateScenarioBuilder(
            data={"Default Ruleset": default_ruleset},
            command_context=command_context,
        ).apply(study_data=empty_study)
        assert output.status, output.message

        remove_area_command: ICommand = RemoveArea(id=area_id2, command_context=command_context)
        output = remove_area_command.apply(study_data=empty_study)
        assert output.status, output.message
        assert dirhash(empty_study.config.study_path, "md5") == hash_before_removal

        actual_cfg = empty_study.tree.get(depth=999)
        assert actual_cfg == empty_study_cfg


def test_match(command_context: CommandContext):
    base = RemoveArea(id="foo", command_context=command_context)
    other_match = RemoveArea(id="foo", command_context=command_context)
    other_not_match = RemoveArea(id="bar", command_context=command_context)
    other_other = RemoveLink(area1="id", area2="id2", command_context=command_context)
    assert base.match(other_match)
    assert not base.match(other_not_match)
    assert not base.match(other_other)
    assert base.match_signature() == "remove_area%foo"
    assert base.get_inner_matrices() == []


def test_create_diff(command_context: CommandContext):
    base = RemoveArea(id="foo", command_context=command_context)
    other_match = RemoveArea(id="foo", command_context=command_context)
    assert base.create_diff(other_match) == []
