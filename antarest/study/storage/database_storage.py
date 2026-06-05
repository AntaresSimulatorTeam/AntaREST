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
import logging
import shutil
import uuid
from pathlib import Path
from typing import BinaryIO, Iterator

from antares.study.version import StudyVersion
from sqlalchemy import select
from typing_extensions import override

from antarest.core.config import Config
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.matrixstore.model import MatrixReference
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.dao.database.database_study_factory_dao import DatabaseStudyDaoFactory
from antarest.study.dao.database.models.area import LOAD_TABLE, MISC_GEN_TABLE, RESERVES_TABLE, SOLAR_TABLE, WIND_TABLE
from antarest.study.dao.database.models.binding_constraint import (
    BINDING_CONSTRAINT_EQ_MATRIX_TABLE,
    BINDING_CONSTRAINT_GT_MATRIX_TABLE,
    BINDING_CONSTRAINT_LT_MATRIX_TABLE,
    BINDING_CONSTRAINT_VALUES_MATRIX_TABLE,
)
from antarest.study.dao.database.models.hydro import (
    HYDRO_CREDIT_MODULATIONS_TABLE,
    HYDRO_ENERGY_TABLE,
    HYDRO_INFLOW_PATTERN_TABLE,
    HYDRO_MAX_DAILY_GEN_ENERGY_TABLE,
    HYDRO_MAX_DAILY_PUMP_ENERGY_TABLE,
    HYDRO_MAX_HOURLY_GEN_POWER_TABLE,
    HYDRO_MAX_HOURLY_PUMP_POWER_TABLE,
    HYDRO_MAXPOWER_TABLE,
    HYDRO_MINGEN_TABLE,
    HYDRO_MODULATION_TABLE,
    HYDRO_RESERVOIR_TABLE,
    HYDRO_RUN_OF_RIVER_TABLE,
    HYDRO_WATER_VALUES_TABLE,
)
from antarest.study.dao.database.models.link import (
    LINK_DIRECT_CAPACITY_TABLE,
    LINK_INDIRECT_CAPACITY_TABLE,
    LINK_SERIES_TABLE,
)
from antarest.study.dao.database.models.renewable import RENEWABLE_SERIES_TABLE
from antarest.study.dao.database.models.reserve_need import RESERVE_NEED_MATRIX_TABLE
from antarest.study.dao.database.models.st_storage import (
    COST_INJECTION_TABLE,
    COST_LEVEL_TABLE,
    COST_VARIATION_INJECTION_TABLE,
    COST_VARIATION_WITHDRAWAL_TABLE,
    COST_WITHDRAWAL_TABLE,
    INFLOWS_TABLE,
    LOWER_RULE_CURVE_TABLE,
    PMAX_INJECTION_TABLE,
    PMAX_WITHDRAWAL_TABLE,
    ST_STORAGE_ADDITIONAL_CONSTRAINT_MATRIX_TABLE,
    UPPER_RULE_CURVE_TABLE,
)
from antarest.study.dao.database.models.thermal import (
    THERMAL_CO2_COST_TABLE,
    THERMAL_FUEL_COST_TABLE,
    THERMAL_MODULATION_TABLE,
    THERMAL_PREPRO_TABLE,
    THERMAL_SERIES_TABLE,
)
from antarest.study.dao.database.models.xpansion import XPANSION_CAPACITY_TABLE, XPANSION_WEIGHT_TABLE
from antarest.study.dao.file.file_study_factory_dao import FileStudyDaoFactory
from antarest.study.dao.study_conversion.study_converter import StudyConverter
from antarest.study.model import RawStudy, Study, StudyMetadataCreation
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.study_storage_interface import IStudyStorage
from antarest.study.storage.utils import extract_data_to_dir, update_study_from_raw_metadata

logger = logging.getLogger(__name__)


MATRIX_TABLES = [
    LOAD_TABLE,
    SOLAR_TABLE,
    WIND_TABLE,
    RESERVES_TABLE,
    MISC_GEN_TABLE,
    LINK_SERIES_TABLE,
    LINK_DIRECT_CAPACITY_TABLE,
    LINK_INDIRECT_CAPACITY_TABLE,
    THERMAL_PREPRO_TABLE,
    THERMAL_MODULATION_TABLE,
    THERMAL_SERIES_TABLE,
    THERMAL_FUEL_COST_TABLE,
    THERMAL_CO2_COST_TABLE,
    RENEWABLE_SERIES_TABLE,
    RESERVE_NEED_MATRIX_TABLE,
    PMAX_INJECTION_TABLE,
    PMAX_WITHDRAWAL_TABLE,
    LOWER_RULE_CURVE_TABLE,
    UPPER_RULE_CURVE_TABLE,
    INFLOWS_TABLE,
    COST_INJECTION_TABLE,
    COST_WITHDRAWAL_TABLE,
    COST_LEVEL_TABLE,
    COST_VARIATION_INJECTION_TABLE,
    COST_VARIATION_WITHDRAWAL_TABLE,
    ST_STORAGE_ADDITIONAL_CONSTRAINT_MATRIX_TABLE,
    HYDRO_MAXPOWER_TABLE,
    HYDRO_RESERVOIR_TABLE,
    HYDRO_ENERGY_TABLE,
    HYDRO_RUN_OF_RIVER_TABLE,
    HYDRO_MODULATION_TABLE,
    HYDRO_CREDIT_MODULATIONS_TABLE,
    HYDRO_INFLOW_PATTERN_TABLE,
    HYDRO_WATER_VALUES_TABLE,
    HYDRO_MINGEN_TABLE,
    HYDRO_MAX_HOURLY_GEN_POWER_TABLE,
    HYDRO_MAX_HOURLY_PUMP_POWER_TABLE,
    HYDRO_MAX_DAILY_GEN_ENERGY_TABLE,
    HYDRO_MAX_DAILY_PUMP_ENERGY_TABLE,
    XPANSION_CAPACITY_TABLE,
    XPANSION_WEIGHT_TABLE,
    BINDING_CONSTRAINT_VALUES_MATRIX_TABLE,
    BINDING_CONSTRAINT_LT_MATRIX_TABLE,
    BINDING_CONSTRAINT_GT_MATRIX_TABLE,
    BINDING_CONSTRAINT_EQ_MATRIX_TABLE,
]


class DatabaseStudyStorage(IStudyStorage):
    def __init__(
        self,
        config: Config,
        repository: StudyMetadataRepository,
        matrix_service: ISimpleMatrixService,
        db_dao_factory: DatabaseStudyDaoFactory,
        fs_dao_factory: FileStudyDaoFactory,
    ):
        self._config = config
        self._repository = repository
        self._matrix_service = matrix_service
        self._db_dao_factory = db_dao_factory
        self._fs_dao_factory = fs_dao_factory

    @override
    def copy(self, src_study: Study, new_study: RawStudy) -> RawStudy:
        try:
            source_dao = self._db_dao_factory.get_study_dao(src_study.id, True)
            study_version = StudyVersion.parse(src_study.version)

            # Build the new DB DAO
            metadata = StudyMetadataCreation(id=new_study.id, version=study_version, managed=True)
            new_dao = self._db_dao_factory.create_study_dao(metadata)

            # Copies the inputs
            converter = StudyConverter(
                source_dao=source_dao, new_dao=new_dao, study_version=study_version, matrix_service=self._matrix_service
            )
            converter.convert_study_inputs()

            return new_study

        except Exception as e:
            logger.error("Failed to copy study %s to %s", src_study.id, new_study.id, exc_info=e)
            # Clean up the database
            db.session.rollback()
            self._repository.delete(new_study.id)
            raise e

    @override
    def write_study_for_archive(self, study: RawStudy, dst_path: Path) -> None:
        # Nothing to do
        pass

    @override
    def export_study(self, study: Study, dst_path: Path) -> None:
        source_dao = self._db_dao_factory.get_study_dao(study_id=study.id, is_study_managed=True)
        study_version = StudyVersion.parse(study.version)

        # Create the new FS DAO
        metadata = StudyMetadataCreation(
            id=study.id,
            version=study_version,
            managed=False,  # Means the matrices will be denormalized
            name=study.name,
            author=study.author,
            editor=study.editor,
            created_at=study.created_at,
            updated_at=study.updated_at,
        )
        new_dao = self._fs_dao_factory.export_study(metadata, dst_path)

        # Convert the DB DAO into an FS DAO
        converter = StudyConverter(
            source_dao=source_dao, new_dao=new_dao, study_version=study_version, matrix_service=self._matrix_service
        )
        converter.convert_study_inputs()

    @override
    def get_disk_usage(self, study: Study) -> int:
        return 0

    @override
    def yield_matrix_references(self, study: Study) -> Iterator[MatrixReference]:
        with db():
            for table in MATRIX_TABLES:
                stmt = select(table.c.matrix_id).where(table.c.study_id == study.id)
                rows = db.session.execute(stmt).fetchall()
                for row in rows:
                    description = f"Matrix used inside table {table.name}, for study {study.id}"
                    yield MatrixReference(matrix_id=row.matrix_id, use_description=description)

    @override
    def normalize_study(self, study: Study) -> None:
        # Nothing to do
        pass

    @override
    def import_study(self, study: RawStudy, stream: BinaryIO) -> None:
        dst_path = self._config.storage.tmp_dir / str(uuid.uuid4())

        try:
            # First, extract the stream inside a temporary directory
            extract_data_to_dir(dst_path, stream, self._config.storage.tmp_dir)

            # Build the FS DAO from the extracted data
            source_dao = self._fs_dao_factory.get_dao_from_path(dst_path, study_id=study.id, is_study_managed=True)

            # Update the `Study` object based on the FS DAO
            update_study_from_raw_metadata(study, source_dao.get_file_study())

            # Create the new study inside DB to avoid ForeignKey and StudyNotFound errors
            self._repository.save(study)

            # Build the DB DAO
            metadata = StudyMetadataCreation(id=study.id, version=source_dao.get_version(), managed=True)
            new_dao = self._db_dao_factory.create_study_dao(metadata)

            # Convert the FS DAO into a DB one
            converter = StudyConverter(
                source_dao=source_dao,
                new_dao=new_dao,
                study_version=source_dao.get_version(),
                matrix_service=self._matrix_service,
            )
            converter.convert_study_inputs()

        except Exception as e:
            logger.error("Failed to import study %s", str(study.path), exc_info=e)
            # Clean up the database
            db.session.rollback()
            self._repository.delete(study.id)
            raise e

        finally:
            shutil.rmtree(dst_path, ignore_errors=True)
