import configparser

from antarest.matrixstore.service import MatrixService
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.matrix_constants_generator import (
    GeneratorMatrixConstants,
)
from antarest.study.storage.variantstudy.model.command.create_area import (
    CreateArea,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)


class TestCreateArea:
    def test_validation(self, empty_study: FileStudy):
        pass

    def test_apply(
        self, empty_study: FileStudy, matrix_service: MatrixService
    ):

        command_context = CommandContext(
            generator_matrix_constants=GeneratorMatrixConstants(
                matrix_service=matrix_service
            ),
            matrix_service=matrix_service,
        )
        version = empty_study.config.version
        study_path = empty_study.config.study_path
        area_name = "Area"

        create_area_command: ICommand = CreateArea.parse_obj(
            {
                "area_name": area_name,
                "metadata": {},
                "command_context": command_context,
            }
        )
        output = create_area_command.apply(
            study_data=empty_study,
        )

        # Areas
        assert area_name in empty_study.config.areas

        with open(study_path / "input" / "areas" / "list.txt") as f:
            area_list = f.read().splitlines()
        assert area_name.upper() in area_list

        assert (study_path / "input" / "areas" / area_name).is_dir()
        assert (
            study_path / "input" / "areas" / area_name / "optimization.ini"
        ).exists()
        assert (study_path / "input" / "areas" / area_name / "ui.ini").exists()

        # Hydro
        hydro = configparser.ConfigParser()
        hydro.read(study_path / "input" / "hydro" / "hydro.ini")
        assert int(hydro["inter-daily-breakdown"][area_name]) == 1
        assert int(hydro["intra-daily-modulation"][area_name]) == 24
        assert int(hydro["inter-monthly-breakdown"][area_name]) == 1
        if version > 650:
            assert int(hydro["initialize reservoir date"][area_name]) == 0
            assert int(hydro["leeway low"][area_name]) == 1
            assert int(hydro["leeway up"][area_name]) == 1
            assert int(hydro["pumping efficiency"][area_name]) == 1

        # Allocation
        assert (
            study_path / "input" / "hydro" / "allocation" / f"{area_name}.ini"
        ).exists()
        allocation = configparser.ConfigParser()
        allocation.read(
            study_path / "input" / "hydro" / "allocation" / f"{area_name}.ini"
        )
        assert int(allocation["[allocation"][area_name]) == 1

        # Capacity
        assert (
            study_path
            / "input"
            / "hydro"
            / "common"
            / "capacity"
            / f"maxpower_{area_name}.txt.link"
        ).exists()
        assert (
            study_path
            / "input"
            / "hydro"
            / "common"
            / "capacity"
            / f"reservoir_{area_name}.txt.link"
        ).exists()
        if version > 650:
            assert (
                study_path
                / "input"
                / "hydro"
                / "common"
                / "capacity"
                / f"creditmodulations_{area_name}.txt.link"
            ).exists()
            assert (
                study_path
                / "input"
                / "hydro"
                / "common"
                / "capacity"
                / f"inflowPattern_{area_name}.txt.link"
            ).exists()
            assert (
                study_path
                / "input"
                / "hydro"
                / "common"
                / "capacity"
                / f"waterValues_{area_name}.txt.link"
            ).exists()

        # Prepro
        assert (study_path / "input" / "hydro" / "prepro" / area_name).is_dir()
        assert (
            study_path
            / "input"
            / "hydro"
            / "prepro"
            / area_name
            / "energy.txt.link"
        ).exists()

        allocation = configparser.ConfigParser()
        allocation.read(
            study_path
            / "input"
            / "hydro"
            / "prepro"
            / area_name
            / "prepro.ini"
        )
        assert float(allocation["prepro"]["intermonthly-correlation"]) == 0.5

        # Series
        assert (study_path / "input" / "hydro" / "series" / area_name).is_dir()
        assert (
            study_path
            / "input"
            / "hydro"
            / "series"
            / area_name
            / "mod.txt.link"
        ).exists()
        assert (
            study_path
            / "input"
            / "hydro"
            / "series"
            / area_name
            / "ror.txt.link"
        ).exists()

        # Links
        assert (study_path / "input" / "links" / area_name).is_dir()
        assert (
            study_path / "input" / "links" / area_name / "properties.ini"
        ).exists()

        # Load
        # Prepro
        assert (study_path / "input" / "load" / "prepro" / area_name).is_dir()
        assert (
            study_path
            / "input"
            / "load"
            / "prepro"
            / area_name
            / "conversion.txt.link"
        ).exists()
        assert (
            study_path
            / "input"
            / "load"
            / "prepro"
            / area_name
            / "data.txt.link"
        ).exists()
        assert (
            study_path / "input" / "load" / "prepro" / area_name / "k.txt.link"
        ).exists()
        assert (
            study_path
            / "input"
            / "load"
            / "prepro"
            / area_name
            / "settings.ini"
        ).exists()
        assert (
            study_path
            / "input"
            / "load"
            / "prepro"
            / area_name
            / "translation.txt.link"
        ).exists()

        # Series
        assert (
            study_path
            / "input"
            / "load"
            / "series"
            / f"load_{area_name}.txt.link"
        ).exists()

        # Misc-gen
        assert (
            study_path / "input" / "misc-gen" / f"miscgen-{area_name}.txt.link"
        ).exists()

        # Reserves
        assert (
            study_path / "input" / "reserves" / f"{area_name}.txt.link"
        ).exists()

        # Solar
        # Prepro
        assert (study_path / "input" / "solar" / "prepro" / area_name).is_dir()
        assert (
            study_path
            / "input"
            / "solar"
            / "prepro"
            / area_name
            / "conversion.txt.link"
        ).exists()
        assert (
            study_path
            / "input"
            / "solar"
            / "prepro"
            / area_name
            / "data.txt.link"
        ).exists()
        assert (
            study_path
            / "input"
            / "solar"
            / "prepro"
            / area_name
            / "k.txt.link"
        ).exists()
        assert (
            study_path
            / "input"
            / "solar"
            / "prepro"
            / area_name
            / "settings.ini"
        ).exists()
        assert (
            study_path
            / "input"
            / "solar"
            / "prepro"
            / area_name
            / "translation.txt.link"
        ).exists()

        # Series
        assert (
            study_path
            / "input"
            / "solar"
            / "series"
            / f"solar_{area_name}.txt.link"
        ).exists()

        # Thermal
        assert (
            study_path / "input" / "thermal" / "clusters" / area_name
        ).is_dir()

        assert (
            study_path
            / "input"
            / "thermal"
            / "clusters"
            / area_name
            / "list.ini"
        ).exists()

        # thermal/areas ini file
        assert (study_path / "input" / "thermal" / "areas.ini").exists()

        # Wind
        # Prepro
        assert (study_path / "input" / "wind" / "prepro" / area_name).is_dir()
        assert (
            study_path
            / "input"
            / "wind"
            / "prepro"
            / area_name
            / "conversion.txt.link"
        ).exists()
        assert (
            study_path
            / "input"
            / "wind"
            / "prepro"
            / area_name
            / "data.txt.link"
        ).exists()
        assert (
            study_path / "input" / "wind" / "prepro" / area_name / "k.txt.link"
        ).exists()
        assert (
            study_path
            / "input"
            / "wind"
            / "prepro"
            / area_name
            / "settings.ini"
        ).exists()
        assert (
            study_path
            / "input"
            / "wind"
            / "prepro"
            / area_name
            / "translation.txt.link"
        ).exists()

        # Series
        assert (
            study_path
            / "input"
            / "wind"
            / "series"
            / f"wind_{area_name}.txt.link"
        ).exists()

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
