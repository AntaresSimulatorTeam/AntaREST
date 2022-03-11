from typing import List

from antarest.matrixstore.business.matrix_editor import (
    Operation,
    MatrixSlice,
    MatrixEditor,
)
from antarest.study.business.utils import execute_or_add_commands
from antarest.study.model import Study
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.replace_matrix import (
    ReplaceMatrix,
)
from antarest.study.storage.variantstudy.model.command.utils import (
    strip_matrix_protocol,
)


class MatrixManager:
    def __init__(self, storage_service: StudyStorageService) -> None:
        self.storage_service = storage_service

    def update_matrix(
        self,
        study: Study,
        path: str,
        slices: List[MatrixSlice],
        operation: Operation,
    ) -> None:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        matrix_service = (
            self.storage_service.variant_study_service.command_factory.command_context.matrix_service
        )

        whole_matrix = self.storage_service.get_storage(study).get(
            metadata=study, url=path
        )
        matrix_data = whole_matrix["data"]

        new_matrix_data = MatrixEditor.update_matrix_content_with_slices(
            matrix_data=matrix_data, slices=slices, operation=operation
        )
        new_matrix_id = matrix_service.create(new_matrix_data)

        command = [
            ReplaceMatrix(
                target=path,
                matrix=strip_matrix_protocol(new_matrix_id),
                command_context=self.storage_service.variant_study_service.command_factory.command_context,
            )
        ]

        execute_or_add_commands(
            study=study,
            file_study=file_study,
            commands=command,
            storage_service=self.storage_service,
        )
