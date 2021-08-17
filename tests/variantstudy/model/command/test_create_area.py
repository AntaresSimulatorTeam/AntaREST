import configparser
from pathlib import Path

from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    transform_name_to_id,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_area import (
    CreateArea,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand


class TestCreateArea:
    def test_validation(self, empty_study: FileStudy):
        pass

    def test_apply(self, empty_study: FileStudy):
        version = empty_study.config.version
        study_path = empty_study.config.root_path
        area_name = "Area"
        area_id = transform_name_to_id(area_name)

        # create_area_command: ICommand = CreateArea(name=area_name, metadata={})
        create_area_command: ICommand = CreateArea.parse_obj(
            {"name": area_name, "metadata": {}}
        )
        create_area_command.apply(study_data=empty_study)

        # Areas
        assert area_name in empty_study.config.areas

        with open(study_path / "input" / "areas" / "list.txt") as f:
            area_list = f.read.striplines()
        assert area_name in area_list

        assert (study_path / "input" / "areas" / area_id).is_dir()
        assert (
            study_path / "input" / "areas" / area_id / "optimization.ini"
        ).exists()
        assert (study_path / "input" / "areas" / area_id / "ui.ini").exists()

        # Hydro
        hydro = configparser.ConfigParser()
        hydro.read(study_path / "input" / "hydro" / "hydro.ini")
        int(hydro["inter-daily-breakdown"][area_id]) == 1
        int(hydro["intra-daily-modulation"][area_id]) == 24
        int(hydro["inter-monthly-breakdown"][area_id]) == 1
        if version == 7:
            int(hydro["initialize reservoir date"][area_id]) == 0
            int(hydro["leeway low"][area_id]) == 1
            int(hydro["leeway up"][area_id]) == 1
            int(hydro["pumping efficiency"][area_id]) == 1

        # Allocation
        assert (
            study_path / "input" / "hydro" / "allocation" / f"{area_id}.ini"
        ).exists()
        allocation = configparser.ConfigParser()
        allocation.read(
            study_path / "input" / "hydro" / "allocation" / f"{area_id}.ini"
        )
        assert area_id in allocation["[allocation]"]

        # Capacity
        assert (
            study_path
            / "input"
            / "hydro"
            / "common"
            / "capacity"
            / f"maxpower_{area_id}.txt"
        ).exists()
        assert (
            study_path
            / "input"
            / "hydro"
            / "common"
            / "capacity"
            / f"reservoir_{area_id}.txt"
        ).exists()
        if version == 7:
            assert (
                study_path
                / "input"
                / "hydro"
                / "common"
                / "capacity"
                / f"creditmodulations_{area_id}.txt"
            ).exists()
            assert (
                study_path
                / "input"
                / "hydro"
                / "common"
                / "capacity"
                / f"inflowPattern_{area_id}.txt"
            ).exists()
            assert (
                study_path
                / "input"
                / "hydro"
                / "common"
                / "capacity"
                / f"waterValues_{area_id}.txt"
            ).exists()
            assert (
                study_path
                / "input"
                / "hydro"
                / "common"
                / "capacity"
                / f"maxpower_{area_id}.txt"
            ).exists()
            assert (
                study_path
                / "input"
                / "hydro"
                / "common"
                / "capacity"
                / f"maxpower_{area_id}.txt"
            ).exists()

        # Prepro
        assert (study_path / "input" / "hydro" / "prepro" / area_id).is_dir()
        assert (
            study_path / "input" / "hydro" / "prepro" / area_id / "energy.txt"
        ).exists()

        prepro = configparser.ConfigParser()
        prepro.read(
            study_path / "input" / "hydro" / "allocation" / f"{area_id}.ini"
        )
        assert float(prepro["intermonthly-correlation"]) == 0.5

        # Series
        assert (study_path / "input" / "hydro" / "series" / area_id).is_dir()
        assert (
            study_path / "input" / "hydro" / "series" / area_id / "mod.txt"
        ).exists()
        assert (
            study_path / "input" / "hydro" / "series" / area_id / "ror.txt"
        ).exists()

        # Links
        assert (study_path / "input" / "links" / area_id).is_dir()
        assert (
            study_path / "input" / "links" / area_id / "properties.ini"
        ).exists()

        # Load
        # Prepro
        assert (study_path / "input" / "load" / "prepro" / area_id).is_dir()
        assert (
            study_path
            / "input"
            / "load"
            / "prepro"
            / area_id
            / "conversion.txt"
        ).exists()
        assert (
            study_path / "input" / "load" / "prepro" / area_id / "data.txt"
        ).exists()
        assert (
            study_path / "input" / "load" / "prepro" / area_id / "k.txt"
        ).exists()
        assert (
            study_path / "input" / "load" / "prepro" / area_id / "settings.ini"
        ).exists()
        assert (
            study_path
            / "input"
            / "load"
            / "prepro"
            / area_id
            / "translation.txt"
        ).exists()

        # Series
        assert (
            study_path / "input" / "load" / "series" / f"load_{area_id}.txt"
        ).exists()

        # Misc-gen
        assert (
            study_path / "input" / "misc-gen" / f"miscgen-{area_id}.txt"
        ).exists()

        # Reserves
        assert (study_path / "input" / "reserves" / f"{area_id}.txt").exists()

        # Solar
        # Prepro
        assert (study_path / "input" / "solar" / "prepro" / area_id).is_dir()
        assert (
            study_path
            / "input"
            / "solar"
            / "prepro"
            / area_id
            / "conversion.txt"
        ).exists()
        assert (
            study_path / "input" / "solar" / "prepro" / area_id / "data.txt"
        ).exists()
        assert (
            study_path / "input" / "solar" / "prepro" / area_id / "k.txt"
        ).exists()
        assert (
            study_path
            / "input"
            / "solar"
            / "prepro"
            / area_id
            / "settings.ini"
        ).exists()
        assert (
            study_path
            / "input"
            / "solar"
            / "prepro"
            / area_id
            / "translation.txt"
        ).exists()

        # Series
        assert (
            study_path / "input" / "solar" / "series" / f"solar_{area_id}.txt"
        ).exists()

        # Thermal
        assert (
            study_path / "input" / "thermal" / "clusters" / area_id
        ).is_dir()

        assert (
            study_path
            / "input"
            / "thermal"
            / "clusters"
            / area_id
            / "list.ini"
        ).exists()

        # thermal/areas ini file
        assert (study_path / "input" / "thermal" / "areas.ini").exists()

        # Wind
        # Prepro
        assert (study_path / "input" / "wind" / "prepro" / area_id).is_dir()
        assert (
            study_path
            / "input"
            / "wind"
            / "prepro"
            / area_id
            / "conversion.txt"
        ).exists()
        assert (
            study_path / "input" / "wind" / "prepro" / area_id / "data.txt"
        ).exists()
        assert (
            study_path / "input" / "wind" / "prepro" / area_id / "k.txt"
        ).exists()
        assert (
            study_path / "input" / "wind" / "prepro" / area_id / "settings.ini"
        ).exists()
        assert (
            study_path
            / "input"
            / "wind"
            / "prepro"
            / area_id
            / "translation.txt"
        ).exists()

        # Series
        assert (
            study_path / "input" / "wind" / "series" / f"solar_{area_id}.txt"
        ).exists()
