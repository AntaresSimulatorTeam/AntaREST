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

"""
This module dedicated to variant snapshot generation.
"""

import logging
import uuid
from collections.abc import Sequence
from typing import TYPE_CHECKING, NamedTuple

from antarest.core.exceptions import StudyNotFoundError, UnsupportedOperationOnArchivedStudy, VariantGenerationError
from antarest.core.model import StudyPermissionType
from antarest.core.tasks.service import ITaskNotifier, NoopNotifier
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.dao.api.study_factory_dao import StudyFactoryDao
from antarest.study.model import Study, StudyMetadataUpdate
from antarest.study.storage.utils import (
    assert_permission_on_studies,
    format_timestamp,
    remove_from_cache,
)
from antarest.study.storage.variantstudy.model.dbmodel import (
    CommandBlock,
    VariantStudy,
    VariantStudySnapshot,
    VariantStudySnapshotLineage,
)
from antarest.study.storage.variantstudy.model.model import GenerationResultInfoDTO
from antarest.study.storage.variantstudy.variant_command_generator import apply_commands_to_variant

if TYPE_CHECKING:
    from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService

logger = logging.getLogger(__name__)


class RefStudySearchResult(NamedTuple):
    """
    Result of the search for the reference study.
    """

    ref_study: Study
    cmd_blocks: list[CommandBlock]
    version: int
    lineage: tuple["LineageVersion", ...]
    source_snapshot: "SourceSnapshotToken | None" = None
    force_regenerate: bool = False


class LineageVersion(NamedTuple):
    variant_id: str
    commands_version: int


class SourceSnapshotToken(NamedTuple):
    study_id: str
    generation_id: str


class SourceSnapshotChanged(Exception):
    pass


MAX_SOURCE_SNAPSHOT_RETRIES = 2


def _get_aggregated_command_blocks(variants: Sequence[VariantStudy]) -> list[CommandBlock]:
    return [cmd for variant in variants for cmd in variant.commands]


def _copy_command_blocks(command_blocks: Sequence[CommandBlock]) -> list[CommandBlock]:
    return [CommandBlock(**command_block.to_dict()) for command_block in command_blocks]


def _get_lineage_versions(variants: Sequence[VariantStudy]) -> tuple[LineageVersion, ...]:
    return tuple(
        LineageVersion(variant_id=variant.id, commands_version=variant.commands_version.version) for variant in variants
    )


def _snapshot_matches_lineage(snapshot: VariantStudySnapshot, lineage: tuple[LineageVersion, ...]) -> bool:
    return tuple((entry.variant_id, entry.commands_version) for entry in snapshot.lineage) == lineage


class SnapshotGenerator:
    """
    Helper class used to generate snapshots for variant studies.
    """

    def __init__(self, variant_study_service: "VariantStudyService"):
        self.cache = variant_study_service.cache
        self.variant_study_service = variant_study_service
        self.command_factory = variant_study_service.command_factory
        self.study_factory = variant_study_service.study_factory
        self.repository = variant_study_service.repository

    def generate_snapshot(
        self,
        variant_study_id: str,
        *,
        dao_factory: StudyFactoryDao,
        from_scratch: bool = False,
        notifier: ITaskNotifier = NoopNotifier(),
    ) -> GenerationResultInfoDTO:
        for attempt in range(MAX_SOURCE_SNAPSHOT_RETRIES + 1):
            try:
                return self._generate_snapshot(
                    variant_study_id,
                    dao_factory=dao_factory,
                    from_scratch=from_scratch,
                    notifier=notifier,
                )
            except SourceSnapshotChanged:
                if attempt == MAX_SOURCE_SNAPSHOT_RETRIES:
                    raise VariantGenerationError(
                        f"Source snapshot changed repeatedly while generating variant {variant_study_id}"
                    ) from None
                logger.info(
                    "Source snapshot changed while generating variant '%s'; retrying (%s/%s)",
                    variant_study_id,
                    attempt + 1,
                    MAX_SOURCE_SNAPSHOT_RETRIES,
                )

        raise AssertionError("Unreachable")

    def _generate_snapshot(
        self,
        variant_study_id: str,
        *,
        dao_factory: StudyFactoryDao,
        from_scratch: bool = False,
        notifier: ITaskNotifier = NoopNotifier(),
    ) -> GenerationResultInfoDTO:
        # ATTENTION: since we are making changes to disk, a file lock is needed.
        # The locking is currently done in the `VariantStudyService.generate_task` function
        # when starting the task. However, it is not enough, because the snapshot generation
        # need to read the root study or a snapshot of a variant study which may be modified
        # during the task. Ideally, we should lock the root study and all its descendants,
        # but it is not currently possible to lock studies.
        # The locking done at the task level nevertheless makes it possible to limit the risks.

        logger.info(f"Generating variant study snapshot for '{variant_study_id}'")

        root_study, descendants = self._retrieve_descendants(variant_study_id)
        assert_permission_on_studies([root_study, *descendants], StudyPermissionType.READ)
        if root_study.archived:
            raise UnsupportedOperationOnArchivedStudy(root_study.id)
        search_result = self.search_ref_study(root_study, descendants, from_scratch=from_scratch)

        variant_study = descendants[-1]
        previous_last_executed_command = (
            variant_study.snapshot.last_executed_command if variant_study.snapshot is not None else None
        )
        cmd_blocks = _copy_command_blocks(search_result.cmd_blocks)
        ref_study_id = search_result.ref_study.id

        # Persist this before modifying snapshot data. Commands are copied
        # above so the invalidation commit cannot reload different inputs.
        self.variant_study_service.invalidate_snapshot(variant_study)
        ref_study = self.repository.get(ref_study_id)
        if ref_study is None:
            raise StudyNotFoundError(ref_study_id)
        variant_study = self.repository.get_study_with_commands(variant_study_id, with_snapshot=True)

        try:
            if search_result.force_regenerate:
                self.variant_study_service.create_snapshot(ref_study, variant_study)

            # The snapshot is generated, we also need to de-normalize the matrices.
            study_dao = dao_factory.get_study_dao(variant_study.id, True)

            logger.info(f"Applying commands to the reference study '{ref_study.id}'...")
            results = self._apply_commands(study_dao, variant_study, cmd_blocks)

            # Finally, we can update the database.
            logger.info(f"Saving new snapshot for study {variant_study_id}")
            if search_result.source_snapshot and not self.repository.has_snapshot_generation_id(
                search_result.source_snapshot.study_id,
                search_result.source_snapshot.generation_id,
            ):
                raise SourceSnapshotChanged()

            last_executed_command = None
            if cmd_blocks:
                last_executed_command = cmd_blocks[-1].id
            else:
                last_executed_command = previous_last_executed_command
            variant_study.snapshot = VariantStudySnapshot(
                id=variant_study_id,
                version=search_result.version,
                generation_id=str(uuid.uuid4()),
                last_executed_command=last_executed_command,
                lineage=[
                    VariantStudySnapshotLineage(
                        snapshot_id=variant_study_id,
                        position=position,
                        variant_id=lineage_version.variant_id,
                        commands_version=lineage_version.commands_version,
                    )
                    for position, lineage_version in enumerate(search_result.lineage)
                ],
            )
            self.repository.save(variant_study)

            if results.should_invalidate_cache:
                # We need to remove the cache
                remove_from_cache(self.cache, variant_study_id)
            else:
                study_dao.update_cache()

        except Exception:
            remove_from_cache(self.cache, variant_study_id)
            self.variant_study_service.clear_snapshot(variant_study)
            raise

        else:
            try:
                notifier.notify_message(results.model_dump_json())
            except Exception as exc:
                # This exception is ignored, because it is not critical.
                logger.warning(f"Error while sending notification: {exc}", exc_info=True)

        return results

    def _retrieve_descendants(self, variant_study_id: str) -> tuple[Study, Sequence[VariantStudy]]:
        # Get all ancestors of the current study from bottom to top
        # The first IDs are variant IDs, the last is the root study ID.
        ancestor_ids = self.repository.get_ancestor_or_self_ids(variant_study_id)
        descendant_ids = ancestor_ids[::-1]
        return self.repository.get_study_tree(descendant_ids)

    def _apply_commands(
        self, study_dao: StudyDao, variant_study: VariantStudy, cmd_blocks: list[CommandBlock]
    ) -> GenerationResultInfoDTO:
        commands = [self.command_factory.to_command(cb.to_dto()) for cb in cmd_blocks]
        results = apply_commands_to_variant(commands, study=study_dao, metadata=variant_study)
        if not results.success:
            message = f"Failed to generate variant study {variant_study.id}"
            if results.details:
                detail = results.details[-1]
                if isinstance(detail, (tuple, list)):
                    # old format: LegacyDetailsDTO
                    message += f": {detail[2]}"
                elif isinstance(detail, dict):
                    # new format since v2.17: NewDetailsDTO
                    message += f": {detail['msg']}"
                else:  # pragma: no cover
                    raise NotImplementedError(f"Unexpected detail type: {type(detail)}")
            raise VariantGenerationError(message)

        metadata = StudyMetadataUpdate(
            name=variant_study.name,
            author=variant_study.author,
            editor=variant_study.editor,
            created_at=format_timestamp(variant_study.created_at),
            last_save=format_timestamp(variant_study.updated_at),
        )

        study_dao.update_antares_file(metadata)
        return results

    def search_ref_study(
        self, root_study: Study, descendants: Sequence[VariantStudy], *, from_scratch: bool
    ) -> RefStudySearchResult:
        """
        Search for the reference study and the commands to use for snapshot generation.

        Args:
            root_study: The root study from which the descendants of variants are derived.
            descendants: The list of descendants of variants from top to bottom.
            from_scratch: Whether to generate the snapshot from scratch or not.

        Returns:
            The reference study and the commands to use for snapshot generation.
        """
        current_variant = descendants[-1]
        lineage = _get_lineage_versions(descendants)

        if from_scratch:
            # In the case of a from scratch generation, the root study will be used as the reference study.
            # We need to retrieve all commands from the descendants of variants to apply them on the reference study.
            commands_version = current_variant.commands_version.version
            command_blocks = _get_aggregated_command_blocks(descendants)
            return RefStudySearchResult(
                ref_study=root_study,
                cmd_blocks=command_blocks,
                force_regenerate=True,
                version=commands_version,
                lineage=lineage,
            )

        # 1st case: The variant snapshot is already up to date -> No-op.
        # This is handled via the `variant_study_service` before calling the SnapshotGenerator, so we should not bother.
        # And even if it was the case, the 2nd case will handle it.
        # This way we avoid making unnecessary DB queries.

        # 2nd case: The variant has a snapshot, but it is not up to date.
        # We only have to check if we can reuse the snapshot to minimize the generation time.
        # We can reuse the snapshot if the last executed command is still present in the variant commands list.
        # It's not always the case as the user could have removed a command or replaced them all.
        if current_variant.snapshot is not None and _snapshot_matches_lineage(current_variant.snapshot, lineage):
            if last_executed_cmd_id := current_variant.snapshot.last_executed_command:
                for command_block in current_variant.commands:
                    if command_block.id == last_executed_cmd_id:
                        last_exec_index = command_block.index
                        return RefStudySearchResult(
                            ref_study=current_variant,
                            cmd_blocks=current_variant.commands[last_exec_index + 1 :],
                            force_regenerate=False,
                            version=current_variant.commands_version.version,
                            lineage=lineage,
                        )

        for index in range(len(descendants) - 2, -1, -1):
            candidate = descendants[index]
            candidate_lineage = _get_lineage_versions(descendants[: index + 1])
            if (
                candidate.snapshot is not None
                and candidate.snapshot.generation_id is not None
                and _snapshot_matches_lineage(candidate.snapshot, candidate_lineage)
            ):
                return RefStudySearchResult(
                    ref_study=candidate,
                    cmd_blocks=_get_aggregated_command_blocks(descendants[index + 1 :]),
                    force_regenerate=True,
                    version=current_variant.commands_version.version,
                    lineage=lineage,
                    source_snapshot=SourceSnapshotToken(candidate.id, candidate.snapshot.generation_id),
                )

        # Final case: no usable snapshot is available in the lineage.
        commands_version = current_variant.commands_version.version
        command_blocks = _get_aggregated_command_blocks(descendants)
        return RefStudySearchResult(
            ref_study=root_study,
            cmd_blocks=command_blocks,
            force_regenerate=True,
            version=commands_version,
            lineage=lineage,
        )
