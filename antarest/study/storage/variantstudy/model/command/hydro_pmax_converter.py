# Copyright (c) 2026, RTE (https://www.rte-france.com)
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

from typing import Optional

from typing_extensions import override

from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class HydroPmaxConverter(ICommand):
    """
    Command used to convert hydro-pmax value from daily to hourly and vice versa
    """

    command_name: CommandName = CommandName.CONVERT_HYDRO_PMAX

    hydro_pmax: str

    @override
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        # Mapping to store BOTH matrix IDs per area: {area_id: {"gen": matrix_id, "pump": matrix_id}}
        # hourly_matrix_mapping: dict[str, dict[str, str]] = {}
        # daily_matrix_mapping: dict[str, dict[str, str]] = {}

        # 1 - Get all areas
        """
        # Do that inside DAO class with method something like convert_hydro_pmax
        areas = study_data.get_file_study().config.areas.keys()
        total_areas = len(areas)
        file_study = study_data.get_file_study()

        for index, area_id in enumerate(areas):
            try:
                # we will assume that if hydro_pmax is hourly that we have all files in study
                if self.hydro_pmax == "hourly":
                    try:
                        file_study.tree.delete(["input", "hydro", "series", area_id, "maxHourlyGenPower"])
                        file_study.tree.delete(["input", "hydro", "series", area_id, "maxHourlyPumpPower"])
                        file_study.tree.delete(["input", "hydro", "common", "capacity", f"maxDailyGenEnergy_{area_id}"])
                        file_study.tree.delete(
                            ["input", "hydro", "common", "capacity", f"maxDailyPumpEnergy_{area_id}"]
                        )
                    except ChildNotFoundError:
                        pass
                    except Exception:
                        pass

                    # With this approach is possible to not have hourly and daily matrices so we need to create them both
                    matrix_id_gen = MATRIX_PROTOCOL_PREFIX + self.command_context.matrix_service.create(
                        pd.DataFrame(np.zeros((8760, 1)))
                    )

                    matrix_id_pump = MATRIX_PROTOCOL_PREFIX + self.command_context.matrix_service.create(
                        pd.DataFrame(np.zeros((8760, 1)))
                    )

                    hourly_matrix_mapping[area_id] = {
                        "gen": matrix_id_gen,
                        "pump": matrix_id_pump,
                    }

                    # generate daily matrices
                    matrix_id_gen = MATRIX_PROTOCOL_PREFIX + self.command_context.matrix_service.create(
                        pd.DataFrame(np.full((365, 1), 24))
                    )
                    matrix_id_pump = MATRIX_PROTOCOL_PREFIX + self.command_context.matrix_service.create(
                        pd.DataFrame(np.full((365, 1), 24))
                    )

                    daily_matrix_mapping[area_id] = {
                        "gen": matrix_id_gen,
                        "pump": matrix_id_pump,
                    }

                else:
                    # we assume that if we are doing trainsition from hourly -> daily that we have all files in study
                    # so only what we need to do is to delete the hourly matrices
                    try:
                        file_study.tree.delete(["input", "hydro", "series", area_id, "maxHourlyGenPower"])
                        file_study.tree.delete(["input", "hydro", "series", area_id, "maxHourlyPumpPower"])
                    except ChildNotFoundError:
                        pass
                    except Exception:
                        pass

                if listener:
                    progress = int(((index + 1) / total_areas) * 100)
                    listener.notify_progress(progress)

            except Exception as e:
                return command_failed(f"Error converting hydro-pmax value for area {area_id}: {e}")

        # 3 - Second loop: Once all matrices are written to matrix store, modify input folder
        for area_id, matrices in hourly_matrix_mapping.items():
            if self.hydro_pmax == "hourly":
                try:
                    study_data.save_hydro_max_hourly_gen_power(area_id, matrices["gen"])
                    study_data.save_hydro_max_hourly_pump_power(area_id, matrices["pump"])
                    study_data.save_hydro_max_daily_gen_energy(area_id, daily_matrix_mapping[area_id]["gen"])
                    study_data.save_hydro_max_daily_pump_energy(area_id, daily_matrix_mapping[area_id]["pump"])
                except ChildNotFoundError:
                    # Node may not exist if study version < 9.2 or files don't exist
                    pass
                except Exception:
                    pass

        hydro_pmax_before_change = "daily" if self.hydro_pmax == "hourly" else "hourly"
        return command_succeeded(
            f"Hydro pmax converted from {hydro_pmax_before_change} to {self.hydro_pmax} successfully."
        )
        """

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={"hydro_pmax": self.hydro_pmax},
            study_version=self.study_version,
        )
