from pathlib import Path

from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfigDTO,
    FileStudyTreeConfig,
    Area,
    DistrictSet,
    Simulation,
    BindingConstraintDTO,
)


def test_file_study_tree_config_dto():
    config = FileStudyTreeConfig(
        study_path=Path("test"),
        path=Path("curr_path"),
        study_id="study_id",
        version=700,
        output_path=Path("output_path"),
        areas={
            "a": Area(
                name="a",
                links={},
                thermals=[],
                renewables=[],
                filters_synthesis=[],
                filters_year=[],
            )
        },
        sets={"s": DistrictSet()},
        outputs={
            "o": Simulation(
                name="o",
                date="date",
                mode="mode",
                nbyears=1,
                synthesis=True,
                by_year=True,
                error=True,
                playlist=[0],
            )
        },
        bindings=[BindingConstraintDTO(id="b1", areas=[], clusters=[])],
        store_new_set=False,
        archive_input_series=["?"],
        enr_modelling="aggregated",
    )
    config_dto = FileStudyTreeConfigDTO.from_build_config(config)
    assert list(config_dto.dict().keys()) + ["cache"] == list(
        config.__dict__.keys()
    )
    assert config_dto.to_build_config() == config
