import configparser
from unittest.mock import Mock

import pytest

from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    ENR_MODELLING,
    transform_name_to_id,
    ENR_MODELLING,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.command_reverter import (
    CommandReverter,
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


class TestCreateArea:
    @pytest.mark.parametrize("version", [600, 650, 810, 830, 860])
    @pytest.mark.parametrize("enr_modelling", list(ENR_MODELLING))
    def test_apply(
        self,
        empty_study: FileStudy,
        command_context: CommandContext,
        # pytest parameters
        version,
        enr_modelling,
    ):
        empty_study.config.enr_modelling = enr_modelling.value
        empty_study.config.version = version

        study_path = empty_study.config.study_path
        area_name = "Area"
        area_id = transform_name_to_id(area_name)

        create_area_command: ICommand = CreateArea.parse_obj(
            {
                "area_name": area_name,
                "command_context": command_context,
            }
        )
        output = create_area_command.apply(study_data=empty_study)

        # fmt: off
        # Areas
        assert area_id in empty_study.config.areas

        with open(study_path / "input" / "areas" / "list.txt") as f:
            area_list = f.read().splitlines()
        assert area_name in area_list

        assert (study_path / "input" / "areas" / area_id).is_dir()
        assert (study_path / "input" / "areas" / area_id / "optimization.ini").exists()
        assert (study_path / "input" / "areas" / area_id / "ui.ini").exists()

        # Hydro
        hydro = configparser.ConfigParser()
        hydro.read(study_path / "input" / "hydro" / "hydro.ini")
        assert int(hydro["inter-daily-breakdown"][area_id]) == 1
        assert int(hydro["intra-daily-modulation"][area_id]) == 24
        assert int(hydro["inter-monthly-breakdown"][area_id]) == 1

        # sourcery skip: no-conditionals-in-tests
        if version > 650:
            assert int(hydro["initialize reservoir date"][area_id]) == 0
            assert int(hydro["leeway low"][area_id]) == 1
            assert int(hydro["leeway up"][area_id]) == 1
            assert int(hydro["pumping efficiency"][area_id]) == 1

        correlation = configparser.ConfigParser()
        correlation.read(study_path / "input" / "hydro" / "prepro" / "correlation.ini")
        correlation_dict = {k: v for k, v in correlation.items() if k != "DEFAULT"}
        assert correlation_dict == {
            "general": {"mode": "annual"},
            "annual": {},
        }

        # Allocation
        assert (study_path / "input" / "hydro" / "allocation" / f"{area_id}.ini").exists()
        allocation = configparser.ConfigParser()
        allocation.read(study_path / "input" / "hydro" / "allocation" / f"{area_id}.ini")
        assert int(allocation["[allocation"][area_id]) == 1

        # Capacity
        assert (study_path / "input" / "hydro" / "common" / "capacity" / f"maxpower_{area_id}.txt.link").exists()
        assert (study_path / "input" / "hydro" / "common" / "capacity" / f"reservoir_{area_id}.txt.link").exists()

        # sourcery skip: no-conditionals-in-tests
        if version > 650:
            assert (
                study_path / "input" / "hydro" / "common" / "capacity" / f"creditmodulations_{area_id}.txt.link"
            ).exists()
            assert (
                study_path / "input" / "hydro" / "common" / "capacity" / f"inflowPattern_{area_id}.txt.link"
            ).exists()
            assert (study_path / "input" / "hydro" / "common" / "capacity" / f"waterValues_{area_id}.txt.link").exists()

        # Prepro
        assert (study_path / "input" / "hydro" / "prepro" / area_id).is_dir()
        assert (study_path / "input" / "hydro" / "prepro" / area_id / "energy.txt.link").exists()

        allocation = configparser.ConfigParser()
        allocation.read(study_path / "input" / "hydro" / "prepro" / area_id / "prepro.ini")
        assert float(allocation["prepro"]["intermonthly-correlation"]) == 0.5

        # Series
        assert (study_path / "input" / "hydro" / "series" / area_id).is_dir()
        assert (study_path / "input" / "hydro" / "series" / area_id / "mod.txt.link").exists()
        assert (study_path / "input" / "hydro" / "series" / area_id / "ror.txt.link").exists()

        # Links
        assert (study_path / "input" / "links" / area_id).is_dir()
        assert (study_path / "input" / "links" / area_id / "properties.ini").exists()

        # Load / Solar / Wind
        # sourcery skip: no-loop-in-tests
        for gen_type in ("load", "solar", "wind"):
            # Prepro
            assert (study_path / "input" / gen_type / "prepro" / area_id).is_dir()
            assert (study_path / "input" / gen_type / "prepro" / area_id / "conversion.txt.link").exists()
            assert (study_path / "input" / gen_type / "prepro" / area_id / "data.txt.link").exists()
            assert (study_path / "input" / gen_type / "prepro" / area_id / "k.txt.link").exists()
            assert (study_path / "input" / gen_type / "prepro" / area_id / "settings.ini").exists()
            assert (study_path / "input" / gen_type / "prepro" / area_id / "translation.txt.link").exists()
            # Series
            assert (study_path / "input" / gen_type / "series" / f"{gen_type}_{area_id}.txt.link").exists()

        # Misc-gen
        assert (study_path / "input" / "misc-gen" / f"miscgen-{area_id}.txt.link").exists()

        # Reserves
        assert (study_path / "input" / "reserves" / f"{area_id}.txt.link").exists()

        # Thermal Clusters
        assert (study_path / "input" / "thermal" / "clusters" / area_id).is_dir()
        assert (study_path / "input" / "thermal" / "clusters" / area_id / "list.ini").exists()

        # Renewable Clusters
        if version >= 810 and empty_study.config.enr_modelling == ENR_MODELLING.CLUSTERS.value:
            assert (study_path / "input" / "renewables" / "clusters" / area_id).is_dir()
            assert (study_path / "input" / "renewables" / "clusters" / area_id / "list.ini").exists()

        # thermal/areas ini file
        assert (study_path / "input" / "thermal" / "areas.ini").exists()
        # fmt: on

        assert output.status

        create_area_command: ICommand = CreateArea.parse_obj(
            {
                "area_name": area_name,
                "metadata": {},
                "command_context": command_context,
            }
        )
        output = create_area_command.apply(study_data=empty_study)
        assert not output.status


def test_match(command_context: CommandContext):
    # fmt: off
    base = CreateArea(area_name="foo", command_context=command_context)
    other_match = CreateArea(area_name="foo", command_context=command_context)
    other_not_match = CreateArea(area_name="bar", command_context=command_context)
    other_other = RemoveArea(id="id", command_context=command_context)
    # fmt: on
    assert base.match(other_match)
    assert not base.match(other_not_match)
    assert not base.match(other_other)
    assert base.match_signature() == "create_area%foo"
    assert base.get_inner_matrices() == []


def test_revert(command_context: CommandContext):
    base = CreateArea(area_name="foo", command_context=command_context)
    actual = CommandReverter().revert(base, [], Mock(spec=FileStudy))
    assert actual == [RemoveArea(id="foo", command_context=command_context)]


def test_create_diff(command_context: CommandContext):
    base = CreateArea(area_name="foo", command_context=command_context)
    other_match = CreateArea(area_name="foo", command_context=command_context)
    assert base.create_diff(other_match) == []
