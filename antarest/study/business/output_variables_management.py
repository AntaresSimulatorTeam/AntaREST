# Copyright (c) 2025, RTE (https://www.rte-france.com)
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
import time
from pathlib import Path
from typing import Any

import pandas as pd

from antarest.study.business.aggregator_management import (
    MCAllAreasQueryFile,
    MCAllLinksQueryFile,
    MCIndAreasQueryFile,
    MCIndLinksQueryFile,
    MCRoot,
    QueryFileType,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.date_serializer import (
    FactoryDateSerializer,
    rename_unnamed,
)


class OutputVariablesManager:
    """
    Manage output variables view.
    """

    @staticmethod
    def _filter_files_with_same_prefix(
        files: list[str], file_type_class: type[QueryFileType]
    ) -> dict[QueryFileType, str]:
        file_dict = {}
        for file in files:
            splitted_file_name = file.removesuffix(".txt").split("-")
            if len(splitted_file_name) == 2:
                file_type, freq = splitted_file_name
            else:
                file_type1, file_type2, freq = splitted_file_name
                file_type = f"{file_type1}-{file_type2}"
            file_dict[file_type_class(file_type)] = freq
        return file_dict

    @staticmethod
    def _read_header_only(file_path: Path, mc_root: MCRoot, freq: str, file_type: QueryFileType) -> set[str]:
        csv_file = pd.read_csv(file_path, sep="\t", skiprows=4, header=[0, 1, 2], nrows=0)
        date_serializer = FactoryDateSerializer.create(freq, "")
        _, body = date_serializer.extract_date(csv_file)
        rename_unnamed(body)

        if "details" in file_type.value:
            cols = set()
            for col in body.columns:
                for sub_col in col:
                    if sub_col:
                        cols.add(sub_col.upper())
            return cols

        new_cols = []
        for col in body.columns:
            if mc_root == MCRoot.MC_IND:
                name_to_consider = col[0] if file_type.value == "values" else " ".join(col)
            else:
                name_to_consider = " ".join([col[0], col[2]])
            new_cols.append(name_to_consider.upper().strip())

        return set(new_cols)

    def get_variables_metadata(self, output_path: Path) -> dict[str, Any]:
        start = time.time()

        mc_ind_path = output_path / "economy" / MCRoot.MC_IND.value
        mc_all_path = output_path / "economy" / MCRoot.MC_ALL.value
        # Final dict
        variables: dict[str, Any] = {"mc-ind": {"areas": [], "links": []}, "mc-all": {"areas": [], "links": []}}

        ##########################
        # AREAS
        #########################

        areas_mapping = {
            "details": "thermalClusters",
            "details-res": "renewableClusters",
            "details-STstorage": "shortTermStorages",
            "values": "variables",
            "id": "variables",
        }

        first_mc_ind_path = None
        if mc_ind_path.exists():
            first_mc_year = [d.name for d in mc_ind_path.iterdir()][0]
            first_mc_ind_path = mc_ind_path / first_mc_year

        for mc_path in [first_mc_ind_path, mc_all_path]:
            if mc_path and mc_path.exists():
                mc_root = MCRoot.MC_IND if mc_path == first_mc_ind_path else MCRoot.MC_ALL

                # Areas
                areas_folder = mc_path / "areas"
                if areas_folder.exists():
                    for area in areas_folder.iterdir():
                        areas_dict: dict[str, Any] = {"name": area.name}
                        parent_path = areas_folder / area
                        file_type_class = MCIndAreasQueryFile if mc_root == MCRoot.MC_IND else MCAllAreasQueryFile
                        all_files = [d.name for d in parent_path.iterdir()]
                        filtered_files = self._filter_files_with_same_prefix(all_files, file_type_class)
                        for file_type, freq in filtered_files.items():
                            file_path = parent_path / f"{file_type}-{freq}.txt"
                            cols = self._read_header_only(file_path, mc_root, freq, file_type)
                            key = areas_mapping[file_type.value]
                            areas_dict[key] = areas_dict.get(key, set()) | cols

                        variables[mc_root.value]["areas"].append(areas_dict)

                # Links
                links_folder = mc_path / "links"
                if links_folder.exists():
                    for link_name in links_folder.iterdir():
                        area1, area2 = link_name.name.split("-")
                        links_dict: dict[str, Any] = {"area1Name": area1, "area2Name": area2}
                        parent_path = areas_folder / link_name
                        file_type_klass = MCIndLinksQueryFile if mc_root == MCRoot.MC_IND else MCAllLinksQueryFile
                        all_files = [d.name for d in parent_path.iterdir()]
                        filtered_files = self._filter_files_with_same_prefix(all_files, file_type_klass)
                        for file_type, freq in filtered_files.items():
                            file_path = parent_path / f"{file_type}-{freq}.txt"
                            cols = self._read_header_only(file_path, mc_root, freq, file_type)
                            links_dict["variables"] = links_dict.get("variables", set()) | cols

                        variables[mc_root.value]["links"].append(links_dict)

        end = time.time()
        print(f"Headers duration {end - start} seconds")

        return variables
