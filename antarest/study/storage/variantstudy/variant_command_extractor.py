import logging
from typing import List, Optional, Union

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

        links_commands: List[CommandDTO] = []
        for area_id in study_config.areas:
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

            links_data = study_tree.get(
                ["input", "links", area_id, "properties"]
            )
            for link in area.links:
                link_command = CreateLink(
                    area1=area_id,
                    area2=link,
                    parameters={},
                    command_context=self.command_context,
                ).to_dto()
                link_data = links_data.get(link)
                link_config_command = UpdateConfig(
                    target=f"input/links/{area_id}/properties/{link}",
                    data=link_data,
                    command_context=self.command_context,
                ).to_dto()
                links_commands.append(link_command)
                links_commands.append(link_config_command)
                links_commands.append(
                    self._generate_replace_matrix(
                        study_tree,
                        ["input", "links", area_id, link],
                        self.null_matrix_id,
                    )
                )
            stopwatch.log_elapsed(
                lambda x: logger.info(f"Link command extraction done in {x}ms")
            )

            thermal_data = study_tree.get(
                ["input", "thermal", "clusters", area_id, "list"]
            )
            for thermal in area.thermals:
                prepro = study_tree.get(
                    ["input", "thermal", "prepro", area_id, thermal.id, "data"]
                )
                modulation = study_tree.get(
                    [
                        "input",
                        "thermal",
                        "prepro",
                        area_id,
                        thermal.id,
                        "modulation",
                    ]
                )
                cluster_command = CreateCluster(
                    area_id=area_id,
                    cluster_name=thermal.name,
                    parameters=thermal_data[thermal.name],
                    prepro=VariantCommandsExtractor.get_matrix(prepro),
                    modulation=VariantCommandsExtractor.get_matrix(modulation),
                    command_context=self.command_context,
                ).to_dto()
                study_commands.append(cluster_command)
                study_commands.append(
                    self._generate_replace_matrix(
                        study_tree,
                        [
                            "input",
                            "thermal",
                            "series",
                            area_id,
                            thermal.id,
                            "series",
                        ],
                        strip_matrix_protocol(
                            self.generator_matrix_constants.get_null_matrix()
                        ),
                    )
                )
            stopwatch.log_elapsed(
                lambda x: logger.info(
                    f"Thermal command extraction done in {x}ms"
                )
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
                lambda x: logger.info(
                    f"Prepro command extraction done in {x}ms"
                )
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
                lambda x: logger.info(
                    f"Hydro command extraction done in {x}ms"
                )
            )

        study_commands += links_commands

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
        study_commands.append(
            self._generate_update_config(
                study_tree,
                ["input", "areas", "sets"],
            )
        )

        # binding constraints
        binding_config = study_tree.get(
            ["input", "bindingconstraints", "bindingconstraints"]
        )
        for binding in binding_config.values():
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

        stopwatch.log_elapsed(
            lambda x: logger.info(f"Binding command extraction done in {x}ms")
        )

        stopwatch.log_elapsed(
            lambda x: logger.info(f"Command extraction done in {x}ms"), True
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
