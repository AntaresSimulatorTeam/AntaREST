import json
import logging
import os
import time

import requests
from pathlib import Path
from typing import List, Optional, Union, Callable

from requests import Session

from antarest.core.custom_types import JSON
from antarest.core.utils.utils import StopWatch
from antarest.matrixstore.repository import MatrixContentRepository
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import INode
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import (
    FileStudyTree,
)
from antarest.study.storage.rawstudy.model.filesystem.utils import (
    traverse_tree,
)
from antarest.study.storage.variantstudy.business.matrix_constants_generator import (
    GeneratorMatrixConstants,
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
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
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
from antarest.study.storage.variantstudy.model.model import (
    CommandDTO,
    GenerationResultInfoDTO,
)
from antarest.core.cache.business.local_chache import LocalCache
from antarest.core.config import CacheConfig, Config, StorageConfig
from antarest.matrixstore.model import MatrixDTO, MatrixContent, MatrixData
from antarest.matrixstore.service import ISimpleMatrixService, MatrixService
from antarest.study.common.uri_resolver_service import UriResolverService
from antarest.study.storage.rawstudy.model.filesystem.factory import (
    FileStudy,
    StudyFactory,
)
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    TimeStep,
    BindingConstraintOperator,
)

logger = logging.getLogger(__name__)


class SimpleMatrixService(ISimpleMatrixService):
    def __init__(self, matrix_path: Path):
        self.matrix_path = matrix_path
        assert matrix_path.exists() and matrix_path.is_dir()
        config = Config(storage=StorageConfig(matrixstore=matrix_path))
        self.repo_content = MatrixContentRepository(config)

    def create(self, data: MatrixContent) -> str:
        SimpleMatrixService._initialize_matrix_content(data)
        matrix_hash = self.repo_content.save(data)
        return matrix_hash

    def get(self, id: str) -> Optional[MatrixDTO]:
        data = self.repo_content.get(id)
        if data:
            assert data.columns is not None
            assert data.index is not None
            return MatrixDTO(
                id=id,
                width=len(data.columns),
                height=len(data.index),
                index=data.index,
                columns=data.columns,
                data=data.data,
            )
        else:
            return None

    def delete(self, id: str) -> None:
        self.repo_content.delete(id)


class CLIVariantManager:
    def __init__(
        self,
        host: Optional[str] = None,
        token: Optional[str] = None,
        session: Optional[Session] = None,
    ):
        self.session = session or requests.session()
        self.host = host
        if session is None and host is None:
            raise ValueError("Missing either session or host")
        if token is not None:
            self.session.headers.update({"Authorization": f"Bearer {token}"})

    @staticmethod
    def _generate_update_config(
        study_tree: FileStudyTree,
        url: List[str],
        command_context: CommandContext,
    ) -> CommandDTO:
        data = study_tree.get(url)
        return UpdateConfig(
            target="/".join(url), data=data, command_context=command_context
        ).to_dto()

    @staticmethod
    def _generate_replace_matrix(
        study_tree: FileStudyTree,
        url: List[str],
        command_context: CommandContext,
        default_value: Optional[str] = None,
    ) -> CommandDTO:
        data = study_tree.get(url)
        matrix = CLIVariantManager.get_matrix(data, default_value is None)
        return ReplaceMatrix(
            target="/".join(url),
            matrix=matrix or default_value,
            command_context=command_context,
        ).to_dto()

    @staticmethod
    def _extract_commands_from_study(
        study: FileStudy, matrix_reference_dir: Path
    ) -> List[CommandDTO]:
        stopwatch = StopWatch()
        local_matrix_service = SimpleMatrixService(matrix_reference_dir)
        generator_matrix_constants = GeneratorMatrixConstants(
            local_matrix_service
        )
        command_context = CommandContext(
            generator_matrix_constants=generator_matrix_constants,
            matrix_service=local_matrix_service,
        )
        null_matrix_id = strip_matrix_protocol(
            generator_matrix_constants.get_null_matrix()
        )

        study_tree = study.tree
        study_config = study.config
        study_commands: List[CommandDTO] = []

        study_commands.append(
            CLIVariantManager._generate_update_config(
                study_tree, ["settings", "generaldata"], command_context
            )
        )
        study_commands.append(
            CLIVariantManager._generate_update_config(
                study_tree, ["settings", "scenariobuilder"], command_context
            )
        )
        study_commands.append(
            CLIVariantManager._generate_update_config(
                study_tree, ["layers", "layers"], command_context
            )
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
                command_context=command_context,
            ).to_dto()
            study_commands.append(area_command)
            study_commands.append(
                UpdateConfig(
                    target=f"input/areas/{area_id}/optimization",
                    data=optimization_data,
                    command_context=command_context,
                ).to_dto()
            )
            study_commands.append(
                UpdateConfig(
                    target=f"input/areas/{area_id}/ui",
                    data=ui_data,
                    command_context=command_context,
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
                    command_context=command_context,
                ).to_dto()
                link_data = links_data.get(link)
                link_config_command = UpdateConfig(
                    target=f"input/links/{area_id}/properties/{link}",
                    data=link_data,
                    command_context=command_context,
                ).to_dto()
                links_commands.append(link_command)
                links_commands.append(link_config_command)
                links_commands.append(
                    CLIVariantManager._generate_replace_matrix(
                        study_tree,
                        ["input", "links", area_id, link],
                        command_context,
                        null_matrix_id,
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
                    prepro=CLIVariantManager.get_matrix(prepro),
                    modulation=CLIVariantManager.get_matrix(modulation),
                    command_context=command_context,
                ).to_dto()
                study_commands.append(cluster_command)
                cluster_series_command = ReplaceMatrix(
                    target=f"input/thermal/series/{area_id}/{thermal.id}/series",
                    matrix=CLIVariantManager.get_matrix(
                        study_tree.get(
                            [
                                "input",
                                "thermal",
                                "series",
                                area_id,
                                thermal.id,
                                "series",
                            ]
                        )
                        or strip_matrix_protocol(
                            generator_matrix_constants.get_null_matrix()
                        )
                    ),
                    command_context=command_context,
                ).to_dto()
                study_commands.append(cluster_series_command)
            stopwatch.log_elapsed(
                lambda x: logger.info(
                    f"Thermal command extraction done in {x}ms"
                )
            )

            # load, wind, solar
            for type in ["load", "wind", "solar"]:
                for matrix in ["conversion", "data", "k", "translation"]:
                    study_commands.append(
                        CLIVariantManager._generate_replace_matrix(
                            study_tree,
                            ["input", type, "prepro", area_id, matrix],
                            command_context,
                        )
                    )
                study_commands.append(
                    CLIVariantManager._generate_update_config(
                        study_tree,
                        ["input", type, "prepro", area_id, "settings"],
                        command_context,
                    )
                )
                study_commands.append(
                    CLIVariantManager._generate_replace_matrix(
                        study_tree,
                        ["input", type, "series", f"{type}_{area_id}"],
                        command_context,
                        null_matrix_id,
                    )
                )
            stopwatch.log_elapsed(
                lambda x: logger.info(
                    f"Prepro command extraction done in {x}ms"
                )
            )

            # misc gen / reserves
            study_commands.append(
                CLIVariantManager._generate_replace_matrix(
                    study_tree, ["input", "reserves", area_id], command_context
                )
            )
            study_commands.append(
                CLIVariantManager._generate_replace_matrix(
                    study_tree,
                    ["input", "misc-gen", f"miscgen-{area_id}"],
                    command_context,
                )
            )

            stopwatch.log_elapsed(
                lambda x: logger.info(f"Misc command extraction done in {x}ms")
            )
            # hydro
            # todo

        study_commands += links_commands

        # correlations
        for type in ["load", "wind", "solar", "hydro"]:
            study_commands.append(
                CLIVariantManager._generate_update_config(
                    study_tree,
                    ["input", type, "prepro", "correlation"],
                    command_context,
                )
            )

        # all area config (weird it is found in thermal..)
        study_commands.append(
            CLIVariantManager._generate_update_config(
                study_tree,
                ["input", "thermal", "areas"],
                command_context,
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
                command_context=command_context,
            ).to_dto()
            study_commands.append(binding_constraint_command)
            CLIVariantManager._generate_replace_matrix(
                study_tree,
                ["input", "bindingconstraints", binding["id"]],
                command_context,
            )
        stopwatch.log_elapsed(
            lambda x: logger.info(f"Binding command extraction done in {x}ms")
        )

        stopwatch.log_elapsed(
            lambda x: logger.info(f"Command extraction done in {x}ms"), True
        )
        return study_commands

    @staticmethod
    def extract_commands(study_path: Path, commands_output_dir: Path) -> None:
        if not commands_output_dir.exists():
            commands_output_dir.mkdir(parents=True)
        matrices_dir = commands_output_dir / "matrices"
        matrices_dir.mkdir()

        matrix_service = SimpleMatrixService(matrices_dir)
        matrix_resolver = UriResolverService(matrix_service)
        study_factory = StudyFactory(
            matrix=matrix_service,
            resolver=matrix_resolver,
            cache=LocalCache(CacheConfig()),
        )

        study_config, study_tree = study_factory.create_from_fs(
            study_path, str(study_path), False
        )
        command_list = CLIVariantManager._extract_commands_from_study(
            FileStudy(study_config, study_tree), matrices_dir
        )

        with open(commands_output_dir / "commands.json", "w") as fh:
            json.dump(
                [command.dict(exclude={"id"}) for command in command_list], fh
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

    def parse_commands(self, file: Path) -> List[CommandDTO]:
        with open(file, "r") as fh:
            json_commands = json.load(fh)

        commands: List[CommandDTO] = []
        for command in json_commands:
            commands.append(CommandDTO.parse_obj(command))

        return commands

    def apply_commands(
        self,
        study_id: str,
        commands: List[CommandDTO],
        matrices_dir: Optional[Path],
    ) -> GenerationResultInfoDTO:
        stopwatch = StopWatch()
        study = self.session.get(
            self.build_url(f"/v1/studies/{study_id}")
        ).json()
        assert study is not None

        if matrices_dir:
            matrix_dataset: List[str] = []
            for matrix in os.listdir(matrices_dir):
                with open(matrices_dir / matrix, "r") as fh:
                    matrix_data = json.load(fh)
                    res = self.session.post(
                        self.build_url(f"/v1/matrix"), json=matrix_data
                    )
                    assert res.status_code == 200
                    matrix_id = res.json()
                    assert matrix_id == matrix
                    matrix_dataset.append(matrix_id)
            # TODO could create a dataset from theses matrices using "variant_<study_id>" as name
            # also the matrix could be named after the command name where they are used
            stopwatch.log_elapsed(
                lambda x: logger.info(f"Matrix upload done in {x}ms")
            )

        res = self.session.post(
            self.build_url(f"/v1/studies/{study_id}/commands"),
            json=[command.dict() for command in commands],
        )
        stopwatch.log_elapsed(
            lambda x: logger.info(f"Command upload done in {x}ms")
        )
        assert res.status_code == 200

        res = self.session.put(
            self.build_url(f"/v1/studies/{study_id}/generate?denormalize=true")
        )
        stopwatch.log_elapsed(
            lambda x: logger.info(f"Generation done in {x}ms")
        )
        assert res.status_code == 200
        return GenerationResultInfoDTO.parse_obj(res.json())

    def build_url(self, url: str) -> str:
        if self.host is not None:
            return f"{self.host}/{url}"
        return url
