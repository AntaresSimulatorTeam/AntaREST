import logging
from typing import List, Optional, Union, Tuple

from antarest.core.custom_types import JSON
from antarest.core.utils.utils import StopWatch
from antarest.matrixstore.model import MatrixData
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import (
    FileStudyTree,
)
from antarest.study.storage.variantstudy.business.matrix_constants_generator import (
    GeneratorMatrixConstants,
)
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.model.command.common import (
    TimeStep,
    BindingConstraintOperator,
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
from antarest.study.storage.variantstudy.model.command.create_district import (
    CreateDistrict,
    DistrictBaseFilter,
)
from antarest.study.storage.variantstudy.model.command.create_link import (
    CreateLink,
)
from antarest.study.storage.variantstudy.model.command.replace_matrix import (
    ReplaceMatrix,
)
from antarest.study.storage.variantstudy.model.command.update_config import (
    UpdateConfig,
)
from antarest.study.storage.variantstudy.model.command.utils import (
    strip_matrix_protocol,
)
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)
from antarest.study.storage.variantstudy.model.model import CommandDTO

logger = logging.getLogger(__name__)


class VariantCommandsExtractor:
    def __init__(self, matrix_service: ISimpleMatrixService):
        self.matrix_service = matrix_service
        self.generator_matrix_constants = GeneratorMatrixConstants(
            self.matrix_service
        )
        self.command_context = CommandContext(
            generator_matrix_constants=self.generator_matrix_constants,
            matrix_service=self.matrix_service,
        )
        self.null_matrix_id = strip_matrix_protocol(
            self.generator_matrix_constants.get_null_matrix()
        )

    def extract(self, study: FileStudy) -> List[CommandDTO]:
        stopwatch = StopWatch()
        study_tree = study.tree
        study_config = study.config
        study_commands: List[CommandDTO] = []

        study_commands.append(
            self._generate_update_config(
                study_tree, ["settings", "generaldata"]
            )
        )
        study_commands.append(
            self._generate_update_config(
                study_tree,
                ["settings", "scenariobuilder"],
            )
        )
        study_commands.append(
            self._generate_update_config(study_tree, ["layers", "layers"])
        )
        # todo create something out of variant manager commands to replace single rawnode files ?
        # study_commands.append(
        #     CLIVariantManager._generate_update_config(
        #         study_tree, ["settings", "comments"], command_context
        #     )
        # )
        stopwatch.log_elapsed(
            lambda x: logger.info(f"General command extraction done in {x}ms")
        )

        all_links_commands: List[CommandDTO] = []
        for area_id in study_config.areas:
            area_commands, links_commands = self._extract_area(study, area_id)
            study_commands += area_commands
            all_links_commands += links_commands
        study_commands += all_links_commands

        # correlations
        for type in ["load", "wind", "solar", "hydro"]:
            study_commands.append(
                self._generate_update_config(
                    study_tree,
                    ["input", type, "prepro", "correlation"],
                )
            )

        # sets and all area config (weird it is found in thermal..)
        study_commands.append(
            self._generate_update_config(
                study_tree,
                ["input", "thermal", "areas"],
            )
        )
        for set_id in study_config.sets:
            study_commands += self._extract_district(study, set_id)

        # binding constraints
        binding_config = study_tree.get(
            ["input", "bindingconstraints", "bindingconstraints"]
        )
        for binding_id, binding_data in binding_config.items():
            study_commands += self._extract_binding_constraint(
                study, binding_id, binding_data
            )

        stopwatch.log_elapsed(
            lambda x: logger.info(f"Binding command extraction done in {x}ms")
        )

        stopwatch.log_elapsed(
            lambda x: logger.info(f"Command extraction done in {x}ms"), True
        )
        return study_commands

    def _extract_area(
        self, study: FileStudy, area_id: str
    ) -> Tuple[List[CommandDTO], List[CommandDTO]]:
        stopwatch = StopWatch()
        study_commands: List[CommandDTO] = []
        links_commands: List[CommandDTO] = []
        study_tree = study.tree
        study_config = study.config
        area = study_config.areas[area_id]
        optimization_data = study_tree.get(
            ["input", "areas", area_id, "optimization"]
        )
        ui_data = study_tree.get(["input", "areas", area_id, "ui"])
        area_command = CreateArea(
            area_name=area.name,
            metadata={},
            command_context=self.command_context,
        ).to_dto()
        study_commands.append(area_command)
        study_commands.append(
            UpdateConfig(
                target=f"input/areas/{area_id}/optimization",
                data=optimization_data,
                command_context=self.command_context,
            ).to_dto()
        )
        study_commands.append(
            UpdateConfig(
                target=f"input/areas/{area_id}/ui",
                data=ui_data,
                command_context=self.command_context,
            ).to_dto()
        )
        stopwatch.log_elapsed(
            lambda x: logger.info(f"Area command extraction done in {x}ms")
        )

        links_data = study_tree.get(["input", "links", area_id, "properties"])
        for link in area.links:
            links_commands += self._extract_link(
                study, area_id, link, links_data
            )

        stopwatch.log_elapsed(
            lambda x: logger.info(f"Link command extraction done in {x}ms")
        )
        for thermal in area.thermals:
            study_commands += self._extract_cluster(
                study, area_id, thermal.name
            )
        stopwatch.log_elapsed(
            lambda x: logger.info(f"Thermal command extraction done in {x}ms")
        )

        # load, wind, solar
        for type in ["load", "wind", "solar"]:
            for matrix in ["conversion", "data", "k", "translation"]:
                study_commands.append(
                    self._generate_replace_matrix(
                        study_tree,
                        ["input", type, "prepro", area_id, matrix],
                    )
                )
            study_commands.append(
                self._generate_update_config(
                    study_tree,
                    ["input", type, "prepro", area_id, "settings"],
                )
            )
            study_commands.append(
                self._generate_replace_matrix(
                    study_tree,
                    ["input", type, "series", f"{type}_{area_id}"],
                    self.null_matrix_id,
                )
            )
        stopwatch.log_elapsed(
            lambda x: logger.info(f"Prepro command extraction done in {x}ms")
        )

        # misc gen / reserves
        study_commands.append(
            self._generate_replace_matrix(
                study_tree, ["input", "reserves", area_id]
            )
        )
        study_commands.append(
            self._generate_replace_matrix(
                study_tree,
                ["input", "misc-gen", f"miscgen-{area_id}"],
            )
        )

        stopwatch.log_elapsed(
            lambda x: logger.info(f"Misc command extraction done in {x}ms")
        )
        # hydro
        study_commands += self._extract_hydro(study, area_id)
        stopwatch.log_elapsed(
            lambda x: logger.info(f"Hydro command extraction done in {x}ms")
        )
        return study_commands, links_commands

    def _extract_link(
        self,
        study: FileStudy,
        area1: str,
        area2: str,
        links_data: Optional[JSON] = None,
    ) -> List[CommandDTO]:
        commands: List[CommandDTO] = []
        study_tree = study.tree
        link_command = CreateLink(
            area1=area1,
            area2=area2,
            parameters={},
            command_context=self.command_context,
        ).to_dto()
        link_data = (
            links_data.get(area2)
            if links_data is not None
            else study_tree.get(["input", "links", area1, area2])
        )
        link_config_command = UpdateConfig(
            target=f"input/links/{area1}/properties/{area2}",
            data=link_data,
            command_context=self.command_context,
        ).to_dto()
        commands.append(link_command)
        commands.append(link_config_command)
        commands.append(
            self._generate_replace_matrix(
                study_tree,
                ["input", "links", area1, area2],
                self.null_matrix_id,
            )
        )
        return commands

    def _extract_cluster(
        self, study: FileStudy, area_id: str, thermal_name: str
    ) -> List[CommandDTO]:
        study_commands: List[CommandDTO] = []
        study_tree = study.tree
        study_commands.append(
            CreateCluster(
                area_id=area_id,
                cluster_name=thermal_name,
                parameters={},
                command_context=self.command_context,
            ).to_dto()
        )
        study_commands.append(
            self._generate_update_config(
                study_tree,
                [
                    "input",
                    "thermal",
                    "clusters",
                    area_id,
                    "list",
                    thermal_name,
                ],
            )
        )
        study_commands.append(
            self._generate_replace_matrix(
                study_tree,
                [
                    "input",
                    "thermal",
                    "prepro",
                    area_id,
                    thermal_name,
                    "data",
                ],
                strip_matrix_protocol(
                    self.generator_matrix_constants.get_null_matrix()
                ),
            )
        )
        study_commands.append(
            self._generate_replace_matrix(
                study_tree,
                [
                    "input",
                    "thermal",
                    "prepro",
                    area_id,
                    thermal_name,
                    "modulation",
                ],
                strip_matrix_protocol(
                    self.generator_matrix_constants.get_null_matrix()
                ),
            )
        )
        study_commands.append(
            self._generate_replace_matrix(
                study_tree,
                [
                    "input",
                    "thermal",
                    "series",
                    area_id,
                    thermal_name,
                    "series",
                ],
                strip_matrix_protocol(
                    self.generator_matrix_constants.get_null_matrix()
                ),
            )
        )
        return study_commands

    def _extract_hydro(
        self, study: FileStudy, area_id: str
    ) -> List[CommandDTO]:
        study_tree = study.tree
        commands = [
            self._generate_replace_matrix(
                study_tree,
                [
                    "input",
                    "hydro",
                    "common",
                    "capacity",
                    f"maxpower_{area_id}",
                ],
            ),
            self._generate_replace_matrix(
                study_tree,
                [
                    "input",
                    "hydro",
                    "common",
                    "capacity",
                    f"reservoir_{area_id}",
                ],
            ),
            self._generate_replace_matrix(
                study_tree, ["input", "hydro", "prepro", area_id, "energy"]
            ),
            self._generate_replace_matrix(
                study_tree, ["input", "hydro", "series", area_id, "mod"]
            ),
            self._generate_replace_matrix(
                study_tree, ["input", "hydro", "series", area_id, "ror"]
            ),
            self._generate_update_config(
                study_tree, ["input", "hydro", "prepro", area_id, "prepro"]
            ),
            self._generate_update_config(
                study_tree, ["input", "hydro", "allocation", area_id]
            ),
            self._generate_update_config(
                study_tree,
                [
                    "input",
                    "hydro",
                    "hydro",
                    "inter-monthly-breakdown",
                    area_id,
                ],
            ),
        ]

        if study_tree.config.version > 650:
            commands += [
                self._generate_replace_matrix(
                    study_tree,
                    [
                        "input",
                        "hydro",
                        "common",
                        "capacity",
                        f"creditmodulations_{area_id}",
                    ],
                ),
                self._generate_replace_matrix(
                    study_tree,
                    [
                        "input",
                        "hydro",
                        "common",
                        "capacity",
                        f"inflowPattern_{area_id}",
                    ],
                ),
                self._generate_replace_matrix(
                    study_tree,
                    [
                        "input",
                        "hydro",
                        "common",
                        "capacity",
                        f"waterValues_{area_id}",
                    ],
                ),
            ]

        hydro_config = study_tree.get(["input", "hydro", "hydro"])
        for key in hydro_config:
            if area_id in hydro_config[key]:
                commands.append(
                    self._generate_update_config(
                        study_tree,
                        ["input", "hydro", "hydro", key, area_id],
                    )
                )

        return commands

    def _extract_district(
        self, study: FileStudy, district_id: str
    ) -> List[CommandDTO]:
        study_commands: List[CommandDTO] = []
        study_config = study.config
        study_tree = study.tree
        district_config = study_config.sets[district_id]
        district_fetched_config = study_tree.get(
            ["input", "areas", "sets", district_id]
        )
        study_commands.append(
            CreateDistrict(
                name=district_config.name,
                metadata={},
                base_filter=DistrictBaseFilter.add_all
                if district_config.inverted_set
                else DistrictBaseFilter.remove_all,
                filter_items=district_config.areas or [],
                output=district_config.output,
                comments=district_fetched_config.get("comments", None),
            ).to_dto()
        )
        return study_commands

    def _extract_binding_constraint(
        self,
        study: FileStudy,
        binding_id: str,
        bindings_data: Optional[JSON] = None,
    ) -> List[CommandDTO]:
        study_commands: List[CommandDTO] = []
        study_tree = study.tree
        binding = bindings_data
        if not bindings_data:
            for binding_config in study_tree.get(
                ["input", "bindingconstraints", "bindingconstraints"]
            ).values():
                if binding_config["id"] == binding_id:
                    binding = binding_config
        assert binding is not None
        binding_constraint_command = CreateBindingConstraint(
            name=binding["name"],
            enabled=binding["enabled"],
            time_step=TimeStep(binding["type"]),
            operator=BindingConstraintOperator(binding["operator"]),
            coeffs={
                coeff: [float(el) for el in str(value).split("%")]
                for coeff, value in binding.items()
                if "%" in coeff or "." in coeff
            },
            comments=binding.get("comments", None),
            command_context=self.command_context,
        ).to_dto()
        study_commands.append(binding_constraint_command)
        study_commands.append(
            self._generate_replace_matrix(
                study_tree,
                ["input", "bindingconstraints", binding["id"]],
            )
        )
        return study_commands

    def diff(
        self, base: List[CommandDTO], variant: List[CommandDTO]
    ) -> List[CommandDTO]:
        command_factory = CommandFactory(
            generator_matrix_constants=self.generator_matrix_constants,
            matrix_service=self.matrix_service,
        )
        raise NotImplementedError()

    def _generate_update_config(
        self,
        study_tree: FileStudyTree,
        url: List[str],
    ) -> CommandDTO:
        data = study_tree.get(url)
        return UpdateConfig(
            target="/".join(url),
            data=data,
            command_context=self.command_context,
        ).to_dto()

    def _generate_replace_matrix(
        self,
        study_tree: FileStudyTree,
        url: List[str],
        default_value: Optional[str] = None,
    ) -> CommandDTO:
        data = study_tree.get(url)
        matrix = VariantCommandsExtractor.get_matrix(
            data, default_value is None
        )
        return ReplaceMatrix(
            target="/".join(url),
            matrix=matrix or default_value,
            command_context=self.command_context,
        ).to_dto()

    @staticmethod
    def get_matrix(
        data: Union[JSON, str], raise_on_missing: Optional[bool] = False
    ) -> Optional[Union[str, List[List[MatrixData]]]]:
        if isinstance(data, str):
            return data
        elif isinstance(data, dict):
            if "data" in data:
                assert isinstance(data["data"], list)
                return data["data"]
            else:
                return [[]]
        elif raise_on_missing:
            raise ValueError("Invalid matrix")
        return None
