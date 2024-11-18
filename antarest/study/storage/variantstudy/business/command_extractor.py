# Copyright (c) 2024, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import base64
import logging
import typing as t

import numpy as np

from antarest.core.model import JSON
from antarest.core.utils.utils import StopWatch
from antarest.matrixstore.model import MatrixData
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.model import STUDY_VERSION_6_5, STUDY_VERSION_8_2, STUDY_VERSION_8_7
from antarest.study.storage.patch_service import PatchService
from antarest.study.storage.rawstudy.model.filesystem.config.files import get_playlist
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from antarest.study.storage.variantstudy.business.utils import strip_matrix_protocol
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_binding_constraint import CreateBindingConstraint
from antarest.study.storage.variantstudy.model.command.create_cluster import CreateCluster
from antarest.study.storage.variantstudy.model.command.create_district import CreateDistrict, DistrictBaseFilter
from antarest.study.storage.variantstudy.model.command.create_link import CreateLink
from antarest.study.storage.variantstudy.model.command.create_renewables_cluster import CreateRenewablesCluster
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.replace_matrix import ReplaceMatrix
from antarest.study.storage.variantstudy.model.command.update_comments import UpdateComments
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
from antarest.study.storage.variantstudy.model.command.update_district import UpdateDistrict
from antarest.study.storage.variantstudy.model.command.update_playlist import UpdatePlaylist
from antarest.study.storage.variantstudy.model.command.update_raw_file import UpdateRawFile
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from antarest.study.storage.variantstudy.model.interfaces import ICommandExtractor

logger = logging.getLogger(__name__)


def _find_binding_config(binding_id: str, study_tree: FileStudyTree) -> JSON:
    # noinspection SpellCheckingInspection
    url = ["input", "bindingconstraints", "bindingconstraints"]
    for binding_config in study_tree.get(url).values():
        if binding_config["id"] == binding_id:
            return t.cast(JSON, binding_config)
    raise ValueError(f"Binding constraint '{binding_id}' not found in '{''.join(url)}'")


class CommandExtractor(ICommandExtractor):
    def __init__(self, matrix_service: ISimpleMatrixService, patch_service: PatchService):
        self.matrix_service = matrix_service
        self.generator_matrix_constants = GeneratorMatrixConstants(self.matrix_service)
        self.generator_matrix_constants.init_constant_matrices()
        self.patch_service = patch_service
        self.command_context = CommandContext(
            generator_matrix_constants=self.generator_matrix_constants,
            matrix_service=self.matrix_service,
            patch_service=self.patch_service,
        )

    def extract_area(self, study: FileStudy, area_id: str) -> t.Tuple[t.List[ICommand], t.List[ICommand]]:
        stopwatch = StopWatch()
        study_tree = study.tree
        study_config = study.config
        area = study_config.areas[area_id]
        optimization_data = study_tree.get(["input", "areas", area_id, "optimization"])
        ui_data = study_tree.get(["input", "areas", area_id, "ui"])

        study_commands: t.List[ICommand] = [
            CreateArea(area_name=area.name, command_context=self.command_context, study_version=study_config.version),
            UpdateConfig(
                target=f"input/areas/{area_id}/optimization",
                data=optimization_data,
                command_context=self.command_context,
                study_version=study_config.version,
            ),
            UpdateConfig(
                target=f"input/areas/{area_id}/ui",
                data=ui_data,
                command_context=self.command_context,
                study_version=study_config.version,
            ),
        ]
        stopwatch.log_elapsed(lambda x: logger.info(f"Area command extraction done in {x}s"))

        links_data = study_tree.get(["input", "links", area_id, "properties"])
        links_commands: t.List[ICommand] = []
        for link in area.links:
            links_commands += self.extract_link(study, area_id, link, links_data)

        stopwatch.log_elapsed(lambda x: logger.info(f"Link command extraction done in {x}s"))

        for thermal in area.thermals:
            study_commands += self.extract_cluster(study, area_id, thermal.id)
        stopwatch.log_elapsed(lambda x: logger.info(f"Thermal command extraction done in {x}s"))

        for renewable in area.renewables:
            study_commands += self.extract_renewables_cluster(study, area_id, renewable.id)
        stopwatch.log_elapsed(lambda x: logger.info(f"Renewables command extraction done in {x}s"))

        # load, wind, solar
        null_matrix_id = strip_matrix_protocol(self.generator_matrix_constants.get_null_matrix())
        for gen_type in ["load", "wind", "solar"]:
            for matrix in ["conversion", "data", "k", "translation"]:
                study_commands.append(
                    self.generate_replace_matrix(
                        study_tree,
                        ["input", gen_type, "prepro", area_id, matrix],
                    )
                )
            study_commands.append(
                self.generate_update_config(
                    study_tree,
                    ["input", gen_type, "prepro", area_id, "settings"],
                )
            )
            study_commands.append(
                self.generate_replace_matrix(
                    study_tree,
                    ["input", gen_type, "series", f"{gen_type}_{area_id}"],
                    null_matrix_id,
                )
            )
        stopwatch.log_elapsed(lambda x: logger.info(f"Prepro command extraction done in {x}s"))

        # misc gen / reserves
        study_commands.append(self.generate_replace_matrix(study_tree, ["input", "reserves", area_id]))
        study_commands.append(
            self.generate_replace_matrix(
                study_tree,
                ["input", "misc-gen", f"miscgen-{area_id}"],
            )
        )

        stopwatch.log_elapsed(lambda x: logger.info(f"Misc command extraction done in {x}s"))
        # hydro
        study_commands += self.extract_hydro(study, area_id)
        stopwatch.log_elapsed(lambda x: logger.info(f"Hydro command extraction done in {x}s"))
        return study_commands, links_commands

    def extract_link(
        self,
        study: FileStudy,
        area1: str,
        area2: str,
        links_data: t.Optional[JSON] = None,
    ) -> t.List[ICommand]:
        study_tree = study.tree
        study_version = study.config.version
        link_command = CreateLink(
            area1=area1, area2=area2, parameters={}, command_context=self.command_context, study_version=study_version
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
            study_version=study_version,
        )
        null_matrix_id = strip_matrix_protocol(self.generator_matrix_constants.get_null_matrix())
        commands: t.List[ICommand] = [link_command, link_config_command]
        if study_version < STUDY_VERSION_8_2:
            commands.append(
                self.generate_replace_matrix(
                    study_tree,
                    ["input", "links", area1, area2],
                    null_matrix_id,
                )
            )
        else:
            commands.extend(
                [
                    self.generate_replace_matrix(
                        study_tree,
                        ["input", "links", area1, f"{area2}_parameters"],
                        null_matrix_id,
                    ),
                    self.generate_replace_matrix(
                        study_tree,
                        ["input", "links", area1, "capacities", f"{area2}_direct"],
                        null_matrix_id,
                    ),
                    self.generate_replace_matrix(
                        study_tree,
                        ["input", "links", area1, "capacities", f"{area2}_indirect"],
                        null_matrix_id,
                    ),
                ]
            )
        return commands

    def _extract_cluster(self, study: FileStudy, area_id: str, cluster_id: str, renewables: bool) -> t.List[ICommand]:
        study_tree = study.tree
        if renewables:
            cluster_type = "renewables"  # with a final "s"
            cluster_list = study.config.areas[area_id].renewables
            create_cluster_command = CreateRenewablesCluster
        else:
            cluster_type = "thermal"  # w/o a final "s"
            cluster_list = study.config.areas[area_id].thermals  # type: ignore
            create_cluster_command = CreateCluster  # type: ignore

        cluster = next(iter(c for c in cluster_list if c.id == cluster_id))

        null_matrix_id = strip_matrix_protocol(self.generator_matrix_constants.get_null_matrix())
        # Note that cluster IDs are case-insensitive, but series IDs are in lower case.
        series_id = cluster_id.lower()
        study_commands: t.List[ICommand] = [
            create_cluster_command(
                area_id=area_id,
                cluster_name=cluster.id,
                parameters=cluster.model_dump(by_alias=True, exclude_defaults=True, exclude={"id"}),
                command_context=self.command_context,
                study_version=study_tree.config.version,
            ),
            self.generate_replace_matrix(
                study_tree,
                ["input", cluster_type, "series", area_id, series_id, "series"],
                null_matrix_id,
            ),
        ]
        if not renewables:
            study_commands.extend(
                [
                    self.generate_replace_matrix(
                        study_tree,
                        ["input", cluster_type, "prepro", area_id, series_id, "data"],
                        null_matrix_id,
                    ),
                    self.generate_replace_matrix(
                        study_tree,
                        ["input", cluster_type, "prepro", area_id, series_id, "modulation"],
                        null_matrix_id,
                    ),
                ]
            )
        return study_commands

    def extract_cluster(self, study: FileStudy, area_id: str, thermal_id: str) -> t.List[ICommand]:
        return self._extract_cluster(study, area_id, thermal_id, False)

    def extract_renewables_cluster(self, study: FileStudy, area_id: str, renewables_id: str) -> t.List[ICommand]:
        return self._extract_cluster(study, area_id, renewables_id, True)

    def extract_hydro(self, study: FileStudy, area_id: str) -> t.List[ICommand]:
        study_tree = study.tree
        commands = [
            self.generate_replace_matrix(
                study_tree,
                ["input", "hydro", "common", "capacity", f"maxpower_{area_id}"],
            ),
            self.generate_replace_matrix(
                study_tree,
                ["input", "hydro", "common", "capacity", f"reservoir_{area_id}"],
            ),
            self.generate_replace_matrix(
                study_tree,
                ["input", "hydro", "prepro", area_id, "energy"],
            ),
            self.generate_replace_matrix(
                study_tree,
                ["input", "hydro", "series", area_id, "mod"],
            ),
            self.generate_replace_matrix(
                study_tree,
                ["input", "hydro", "series", area_id, "ror"],
            ),
            self.generate_update_config(
                study_tree,
                ["input", "hydro", "prepro", area_id, "prepro"],
            ),
            self.generate_update_config(
                study_tree,
                ["input", "hydro", "allocation", area_id],
            ),
        ]

        if study_tree.config.version > STUDY_VERSION_6_5:
            commands += [
                self.generate_replace_matrix(
                    study_tree,
                    ["input", "hydro", "common", "capacity", f"creditmodulations_{area_id}"],
                ),
                self.generate_replace_matrix(
                    study_tree,
                    ["input", "hydro", "common", "capacity", f"inflowPattern_{area_id}"],
                ),
                self.generate_replace_matrix(
                    study_tree,
                    ["input", "hydro", "common", "capacity", f"waterValues_{area_id}"],
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

    def extract_district(self, study: FileStudy, district_id: str) -> t.List[ICommand]:
        study_commands: t.List[ICommand] = []
        study_config = study.config
        study_tree = study.tree
        district_config = study_config.sets[district_id]
        base_filter = DistrictBaseFilter.add_all if district_config.inverted_set else DistrictBaseFilter.remove_all
        district_fetched_config = study_tree.get(["input", "areas", "sets", district_id])
        assert district_config.name is not None
        study_commands.append(
            CreateDistrict(
                name=district_config.name,
                base_filter=base_filter,
                filter_items=district_config.areas or [],
                output=district_config.output,
                comments=district_fetched_config.get("comments", None),
                command_context=self.command_context,
                study_version=study_config.version,
            )
        )
        return study_commands

    def extract_comments(self, study: FileStudy) -> t.List[ICommand]:
        study_tree = study.tree
        content = t.cast(bytes, study_tree.get(["settings", "comments"]))
        comments = content.decode("utf-8")
        return [
            UpdateComments(
                comments=comments, command_context=self.command_context, study_version=study_tree.config.version
            )
        ]

    def extract_binding_constraint(
        self,
        study: FileStudy,
        binding_id: str,
        bindings_data: t.Optional[JSON] = None,
    ) -> t.List[ICommand]:
        study_tree = study.tree
        study_version = study.config.version

        # Retrieve binding constraint properties from the study tree,
        # so, field names follow the same convention as the INI file.
        binding: JSON = _find_binding_config(binding_id, study_tree) if bindings_data is None else bindings_data

        # Extract the binding constraint ID, which is recalculated from the name in the command
        bc_id = binding.pop("id")

        # Extract binding constraint terms, which keys contain "%" or "."
        terms = {}
        for term_id, value in sorted(binding.items()):
            if "%" in term_id or "." in term_id:
                weight, _, offset = str(value).partition("%")
                term_value = [float(weight), int(offset)] if offset else [float(weight)]
                terms[term_id] = term_value
                del binding[term_id]

        # Extract the matrices associated with the binding constraint
        if study_version < STUDY_VERSION_8_7:
            urls = {"values": ["input", "bindingconstraints", bc_id]}
        else:
            urls = {
                "less_term_matrix": ["input", "bindingconstraints", f"{bc_id}_lt"],
                "greater_term_matrix": ["input", "bindingconstraints", f"{bc_id}_gt"],
                "equal_term_matrix": ["input", "bindingconstraints", f"{bc_id}_eq"],
            }

        matrices: t.Dict[str, t.List[t.List[float]]] = {}
        for name, url in urls.items():
            matrix = study_tree.get(url)
            if matrix is not None:
                matrices[name] = matrix["data"]

        # Create the command to create the binding constraint
        kwargs = {
            **binding,
            **matrices,
            "coeffs": terms,
            "command_context": self.command_context,
            "study_version": study_version,
        }
        create_cmd = CreateBindingConstraint.model_validate(kwargs)

        return [create_cmd]

    def generate_update_config(self, study_tree: FileStudyTree, url: t.List[str]) -> ICommand:
        data = study_tree.get(url)
        return UpdateConfig(
            target="/".join(url),
            data=data,
            command_context=self.command_context,
            study_version=study_tree.config.version,
        )

    def generate_update_raw_file(self, study_tree: FileStudyTree, url: t.List[str]) -> ICommand:
        data = study_tree.get(url)
        return UpdateRawFile(
            target="/".join(url),
            b64Data=base64.b64encode(t.cast(bytes, data)).decode("utf-8"),
            command_context=self.command_context,
            study_version=study_tree.config.version,
        )

    def generate_update_comments(
        self,
        study_tree: FileStudyTree,
    ) -> ICommand:
        content = t.cast(bytes, study_tree.get(["settings", "comments"]))
        comments = content.decode("utf-8")
        return UpdateComments(
            comments=comments, command_context=self.command_context, study_version=study_tree.config.version
        )

    def generate_update_playlist(
        self,
        study_tree: FileStudyTree,
    ) -> ICommand:
        config = study_tree.get(["settings", "generaldata"])
        playlist = get_playlist(config)
        return UpdatePlaylist(
            items=list(playlist.keys()) if playlist else None,
            weights=({year: weight for year, weight in playlist.items() if weight != 1} if playlist else None),
            active=bool(playlist and len(playlist) > 0),
            reverse=False,
            command_context=self.command_context,
            study_version=study_tree.config.version,
        )

    def generate_replace_matrix(
        self,
        study_tree: FileStudyTree,
        url: t.List[str],
        default_value: t.Optional[str] = None,
    ) -> ICommand:
        data = study_tree.get(url)
        if isinstance(data, str):
            matrix = data
        elif isinstance(data, dict):
            matrix = data["data"] if "data" in data else [[]]
        else:
            matrix = [[]] if default_value is None else default_value
        if isinstance(matrix, np.ndarray):
            matrix = t.cast(t.List[t.List[MatrixData]], matrix.tolist())
        return ReplaceMatrix(
            target="/".join(url),
            matrix=matrix,
            command_context=self.command_context,
            study_version=study_tree.config.version,
        )

    def generate_update_district(
        self,
        study: FileStudy,
        district_id: str,
    ) -> ICommand:
        study_config = study.config
        study_tree = study.tree
        district_config = study_config.sets[district_id]
        district_fetched_config = study_tree.get(["input", "areas", "sets", district_id])
        assert district_config.name is not None
        return UpdateDistrict(
            id=district_config.name,
            base_filter=DistrictBaseFilter.add_all if district_config.inverted_set else DistrictBaseFilter.remove_all,
            filter_items=district_config.areas or [],
            output=district_config.output,
            comments=district_fetched_config.get("comments", None),
            command_context=self.command_context,
            study_version=study_tree.config.version,
        )
