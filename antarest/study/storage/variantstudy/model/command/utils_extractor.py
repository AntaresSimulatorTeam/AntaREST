import base64
import logging
from typing import Optional, List, Tuple, Union, cast

from antarest.core.model import JSON
from antarest.core.utils.utils import StopWatch, assert_this
from antarest.matrixstore.model import MatrixData
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.storage.patch_service import PatchService
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import (
    FileStudyTree,
)
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
from antarest.study.storage.variantstudy.model.command.create_district import (
    DistrictBaseFilter,
    CreateDistrict,
)
from antarest.study.storage.variantstudy.model.command.create_link import (
    CreateLink,
)
from antarest.study.storage.variantstudy.model.command.create_renewables_cluster import (
    CreateRenewablesCluster,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.replace_matrix import (
    ReplaceMatrix,
)
from antarest.study.storage.variantstudy.model.command.update_comments import (
    UpdateComments,
)
from antarest.study.storage.variantstudy.model.command.update_config import (
    UpdateConfig,
)
from antarest.study.storage.variantstudy.model.command.update_raw_file import (
    UpdateRawFile,
)
from antarest.study.storage.variantstudy.model.command.utils import (
    strip_matrix_protocol,
)
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)
from antarest.study.storage.variantstudy.model.interfaces import (
    ICommandExtractor,
)

logger = logging.getLogger(__name__)


class CommandExtraction(ICommandExtractor):
    def __init__(
        self, matrix_service: ISimpleMatrixService, patch_service: PatchService
    ):
        self.matrix_service = matrix_service
        self.generator_matrix_constants = GeneratorMatrixConstants(
            self.matrix_service
        )
        self.patch_service = patch_service
        self.command_context = CommandContext(
            generator_matrix_constants=self.generator_matrix_constants,
            matrix_service=self.matrix_service,
            patch_service=self.patch_service,
        )
        self.null_matrix_id = strip_matrix_protocol(
            self.generator_matrix_constants.get_null_matrix()
        )

    def extract_area(
        self, study: FileStudy, area_id: str
    ) -> Tuple[List[ICommand], List[ICommand]]:
        stopwatch = StopWatch()
        study_commands: List[ICommand] = []
        links_commands: List[ICommand] = []
        study_tree = study.tree
        study_config = study.config
        area = study_config.areas[area_id]
        optimization_data = study_tree.get(
            ["input", "areas", area_id, "optimization"]
        )
        ui_data = study_tree.get(["input", "areas", area_id, "ui"])
        area_command = CreateArea(
            area_name=area.name,
            command_context=self.command_context,
        )
        study_commands.append(area_command)
        study_commands.append(
            UpdateConfig(
                target=f"input/areas/{area_id}/optimization",
                data=optimization_data,
                command_context=self.command_context,
            )
        )
        study_commands.append(
            UpdateConfig(
                target=f"input/areas/{area_id}/ui",
                data=ui_data,
                command_context=self.command_context,
            )
        )
        stopwatch.log_elapsed(
            lambda x: logger.info(f"Area command extraction done in {x}s")
        )

        links_data = study_tree.get(["input", "links", area_id, "properties"])
        for link in area.links:
            links_commands += self.extract_link(
                study, area_id, link, links_data
            )

        stopwatch.log_elapsed(
            lambda x: logger.info(f"Link command extraction done in {x}s")
        )
        for thermal in area.thermals:
            study_commands += self.extract_cluster(study, area_id, thermal.id)
        stopwatch.log_elapsed(
            lambda x: logger.info(f"Thermal command extraction done in {x}s")
        )

        for renewable in area.renewables:
            study_commands += self.extract_renewables_cluster(
                study, area_id, renewable.id
            )
        stopwatch.log_elapsed(
            lambda x: logger.info(
                f"Renewables command extraction done in {x}s"
            )
        )

        # load, wind, solar
        for type in ["load", "wind", "solar"]:
            for matrix in ["conversion", "data", "k", "translation"]:
                study_commands.append(
                    self.generate_replace_matrix(
                        study_tree,
                        ["input", type, "prepro", area_id, matrix],
                    )
                )
            study_commands.append(
                self.generate_update_config(
                    study_tree,
                    ["input", type, "prepro", area_id, "settings"],
                )
            )
            study_commands.append(
                self.generate_replace_matrix(
                    study_tree,
                    ["input", type, "series", f"{type}_{area_id}"],
                    self.null_matrix_id,
                )
            )
        stopwatch.log_elapsed(
            lambda x: logger.info(f"Prepro command extraction done in {x}s")
        )

        # misc gen / reserves
        study_commands.append(
            self.generate_replace_matrix(
                study_tree, ["input", "reserves", area_id]
            )
        )
        study_commands.append(
            self.generate_replace_matrix(
                study_tree,
                ["input", "misc-gen", f"miscgen-{area_id}"],
            )
        )

        stopwatch.log_elapsed(
            lambda x: logger.info(f"Misc command extraction done in {x}s")
        )
        # hydro
        study_commands += self.extract_hydro(study, area_id)
        stopwatch.log_elapsed(
            lambda x: logger.info(f"Hydro command extraction done in {x}s")
        )
        return study_commands, links_commands

    def extract_link(
        self,
        study: FileStudy,
        area1: str,
        area2: str,
        links_data: Optional[JSON] = None,
    ) -> List[ICommand]:
        commands: List[ICommand] = []
        study_tree = study.tree
        link_command = CreateLink(
            area1=area1,
            area2=area2,
            parameters={},
            command_context=self.command_context,
        )
        link_data = (
            links_data.get(area2)
            if links_data is not None
            else study_tree.get(["input", "links", area1, "properties", area2])
        )
        link_config_command = UpdateConfig(
            target=f"input/links/{area1}/properties/{area2}",
            data=link_data,
            command_context=self.command_context,
        )
        commands.append(link_command)
        commands.append(link_config_command)
        if study.config.version < 820:
            commands.append(
                self.generate_replace_matrix(
                    study_tree,
                    ["input", "links", area1, area2],
                    self.null_matrix_id,
                )
            )
        else:
            commands.append(
                self.generate_replace_matrix(
                    study_tree,
                    ["input", "links", area1, f"{area2}_parameters"],
                    self.null_matrix_id,
                )
            )
            commands.append(
                self.generate_replace_matrix(
                    study_tree,
                    ["input", "links", area1, "capacities", f"{area2}_direct"],
                    self.null_matrix_id,
                )
            )
            commands.append(
                self.generate_replace_matrix(
                    study_tree,
                    [
                        "input",
                        "links",
                        area1,
                        "capacities",
                        f"{area2}_indirect",
                    ],
                    self.null_matrix_id,
                )
            )

        return commands

    def _extract_cluster(
        self, study: FileStudy, area_id: str, cluster_id: str, renewables: bool
    ) -> List[ICommand]:
        study_commands: List[ICommand] = []
        study_tree = study.tree
        cluster_name = cluster_id

        cluster_type = "renewables" if renewables else "thermal"
        cluster_list = (
            study.config.areas[area_id].thermals
            if not renewables
            else study.config.areas[area_id].renewables
        )
        create_cluster_command = (
            CreateCluster if not renewables else CreateRenewablesCluster
        )

        for cluster in cluster_list:
            if cluster.id == cluster_id:
                cluster_name = cluster.name
                break

        assert_this(cluster_name is not None)
        study_commands.append(
            create_cluster_command(
                area_id=area_id,
                cluster_name=cluster_name,
                parameters={},
                command_context=self.command_context,
            )
        )
        study_commands.append(
            self.generate_update_config(
                study_tree,
                [
                    "input",
                    cluster_type,
                    "clusters",
                    area_id,
                    "list",
                    cluster_name,
                ],
            )
        )
        study_commands.append(
            self.generate_replace_matrix(
                study_tree,
                [
                    "input",
                    cluster_type,
                    "series",
                    area_id,
                    cluster_id,
                    "series",
                ],
                strip_matrix_protocol(
                    self.generator_matrix_constants.get_null_matrix()
                ),
            )
        )
        if not renewables:
            study_commands.append(
                self.generate_replace_matrix(
                    study_tree,
                    [
                        "input",
                        cluster_type,
                        "prepro",
                        area_id,
                        cluster_id,
                        "data",
                    ],
                    strip_matrix_protocol(
                        self.generator_matrix_constants.get_null_matrix()
                    ),
                )
            )
            study_commands.append(
                self.generate_replace_matrix(
                    study_tree,
                    [
                        "input",
                        cluster_type,
                        "prepro",
                        area_id,
                        cluster_id,
                        "modulation",
                    ],
                    strip_matrix_protocol(
                        self.generator_matrix_constants.get_null_matrix()
                    ),
                )
            )
        return study_commands

    def extract_cluster(
        self, study: FileStudy, area_id: str, thermal_id: str
    ) -> List[ICommand]:
        return self._extract_cluster(study, area_id, thermal_id, False)

    def extract_renewables_cluster(
        self, study: FileStudy, area_id: str, renewables_id: str
    ) -> List[ICommand]:
        return self._extract_cluster(study, area_id, renewables_id, True)

    def extract_hydro(self, study: FileStudy, area_id: str) -> List[ICommand]:
        study_tree = study.tree
        commands = [
            self.generate_replace_matrix(
                study_tree,
                [
                    "input",
                    "hydro",
                    "common",
                    "capacity",
                    f"maxpower_{area_id}",
                ],
            ),
            self.generate_replace_matrix(
                study_tree,
                [
                    "input",
                    "hydro",
                    "common",
                    "capacity",
                    f"reservoir_{area_id}",
                ],
            ),
            self.generate_replace_matrix(
                study_tree, ["input", "hydro", "prepro", area_id, "energy"]
            ),
            self.generate_replace_matrix(
                study_tree, ["input", "hydro", "series", area_id, "mod"]
            ),
            self.generate_replace_matrix(
                study_tree, ["input", "hydro", "series", area_id, "ror"]
            ),
            self.generate_update_config(
                study_tree, ["input", "hydro", "prepro", area_id, "prepro"]
            ),
            self.generate_update_config(
                study_tree, ["input", "hydro", "allocation", area_id]
            ),
        ]

        if study_tree.config.version > 650:
            commands += [
                self.generate_replace_matrix(
                    study_tree,
                    [
                        "input",
                        "hydro",
                        "common",
                        "capacity",
                        f"creditmodulations_{area_id}",
                    ],
                ),
                self.generate_replace_matrix(
                    study_tree,
                    [
                        "input",
                        "hydro",
                        "common",
                        "capacity",
                        f"inflowPattern_{area_id}",
                    ],
                ),
                self.generate_replace_matrix(
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
                    self.generate_update_config(
                        study_tree,
                        ["input", "hydro", "hydro", key, area_id],
                    )
                )

        return commands

    def extract_district(
        self, study: FileStudy, district_id: str
    ) -> List[ICommand]:
        study_commands: List[ICommand] = []
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
                command_context=self.command_context,
            )
        )
        return study_commands

    def extract_comments(self, study: FileStudy) -> List[ICommand]:
        study_tree = study.tree
        return [
            UpdateComments(
                comments=study_tree.get(["settings", "comments"]),
                command_context=self.command_context,
            )
        ]

    def extract_binding_constraint(
        self,
        study: FileStudy,
        binding_id: str,
        bindings_data: Optional[JSON] = None,
    ) -> List[ICommand]:
        study_commands: List[ICommand] = []
        study_tree = study.tree
        binding = bindings_data
        if not bindings_data:
            for binding_config in study_tree.get(
                ["input", "bindingconstraints", "bindingconstraints"]
            ).values():
                if binding_config["id"] == binding_id:
                    binding = binding_config
                    break
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
        )
        study_commands.append(binding_constraint_command)
        study_commands.append(
            self.generate_replace_matrix(
                study_tree,
                ["input", "bindingconstraints", binding["id"]],
            )
        )
        return study_commands

    def generate_update_config(
        self,
        study_tree: FileStudyTree,
        url: List[str],
    ) -> ICommand:
        data = study_tree.get(url)
        return UpdateConfig(
            target="/".join(url),
            data=data,
            command_context=self.command_context,
        )

    def generate_update_rawfile(
        self, study_tree: FileStudyTree, url: List[str]
    ) -> ICommand:
        data = study_tree.get(url)
        return UpdateRawFile(
            target="/".join(url),
            b64Data=base64.b64encode(cast(bytes, data)).decode("utf-8"),
            command_context=self.command_context,
        )

    def generate_update_comments(
        self,
        study_tree: FileStudyTree,
    ) -> ICommand:
        url = ["settings", "comments"]
        comments = study_tree.get(url)
        return UpdateComments(
            comments=comments,
            command_context=self.command_context,
        )

    def generate_replace_matrix(
        self,
        study_tree: FileStudyTree,
        url: List[str],
        default_value: Optional[str] = None,
    ) -> ICommand:
        data = study_tree.get(url)
        matrix = CommandExtraction.get_matrix(data, default_value is None)
        return ReplaceMatrix(
            target="/".join(url),
            matrix=matrix or default_value,
            command_context=self.command_context,
        )

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
