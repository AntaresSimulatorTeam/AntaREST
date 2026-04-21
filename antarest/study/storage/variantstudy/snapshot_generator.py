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
import shutil
from collections.abc import Sequence
from typing import TYPE_CHECKING, NamedTuple

from antarest.core.exceptions import VariantGenerationError
from antarest.core.model import StudyPermissionType
from antarest.core.tasks.service import ITaskNotifier, NoopNotifier
from antarest.core.utils.utils import current_time
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.dao.api.study_factory_dao import StudyFactoryDao
from antarest.study.model import Study, StudyMetadataUpdate
from antarest.study.storage.utils import (
    assert_permission_on_studies,
    format_timestamp,
    remove_from_cache,
)
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.dbmodel import CommandBlock, VariantStudy, VariantStudySnapshot
from antarest.study.storage.variantstudy.model.model import GenerationResultInfoDTO
from antarest.study.storage.variantstudy.variant_command_generator import apply_commands_to_variant

if TYPE_CHECKING:
    from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService

logger = logging.getLogger(__name__)


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
        listener: ICommandListener | None = None,
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
        search_result = search_ref_study(root_study, descendants, from_scratch=from_scratch)

        ref_study = search_result.ref_study
        cmd_blocks = search_result.cmd_blocks

        # Get snapshot directory
        variant_study = descendants[-1]
        snapshot_dir = variant_study.snapshot_dir

        try:
            if search_result.force_regenerate or not snapshot_dir.exists():
                self.variant_study_service.create_snapshot(ref_study)

            # The snapshot is generated, we also need to de-normalize the matrices.
            study_dao = dao_factory.create_study_dao(variant_study)

            logger.info(f"Applying commands to the reference study '{ref_study.id}'...")
            results = self._apply_commands(study_dao, variant_study, cmd_blocks, listener)

            # Finally, we can update the database.
            logger.info(f"Saving new snapshot for study {variant_study_id}")
            variant_study.snapshot = VariantStudySnapshot(
                id=variant_study_id,
                created_at=current_time(),
                last_executed_command=variant_study.commands[-1].id if variant_study.commands else None,
            )
            self.repository.save(variant_study)

            if results.should_invalidate_cache:
                # We need to remove the cache
                remove_from_cache(self.cache, variant_study_id)
            else:
                study_dao.update_cache()

        except Exception:
            remove_from_cache(self.cache, variant_study_id)
            shutil.rmtree(snapshot_dir, ignore_errors=True)
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
        descendants = self.repository.find_variants(descendant_ids)
        root_study = self.repository.one(descendant_ids[0])
        return root_study, descendants

    def _apply_commands(
        self,
        study_dao: StudyDao,
        variant_study: VariantStudy,
        cmd_blocks: Sequence[CommandBlock],
        listener: ICommandListener | None = None,
    ) -> GenerationResultInfoDTO:
        commands = [self.command_factory.to_command(cb.to_dto()) for cb in cmd_blocks]
        results = apply_commands_to_variant(commands, study=study_dao, metadata=variant_study, listener=listener)
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


class RefStudySearchResult(NamedTuple):
    """
    Result of the search for the reference study.
    """

    ref_study: Study
    cmd_blocks: Sequence[CommandBlock]
    force_regenerate: bool = False


def search_ref_study(
    root_study: Study,
    descendants: Sequence[VariantStudy],
    *,
    from_scratch: bool = False,
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
    if not descendants:
        # Edge case where the list of studies is empty.
        return RefStudySearchResult(ref_study=root_study, cmd_blocks=[], force_regenerate=True)

    # The reference study is the root study or a variant study with a valid snapshot
    ref_study: Study

    # The commands to apply on the reference study to generate the current variant
    cmd_blocks: list[CommandBlock]

    if from_scratch:
        # In the case of a from scratch generation, the root study will be used as the reference study.
        # We need to retrieve all commands from the descendants of variants in order to apply them
        # on the reference study.
        return RefStudySearchResult(
            ref_study=root_study,
            cmd_blocks=[c for v in descendants for c in v.commands],
            force_regenerate=True,
        )

    # To reuse the snapshot of the current variant, the last executed command
    # must be one of the commands of the current variant.
    curr_variant = descendants[-1]
    if curr_variant.has_snapshot():
        last_exec_cmd = curr_variant.snapshot.last_executed_command
        command_ids = [c.id for c in curr_variant.commands]
        # If the variant has no command, we can reuse the snapshot if it is recent
        if not last_exec_cmd and not command_ids and curr_variant.is_snapshot_up_to_date():
            return RefStudySearchResult(
                ref_study=curr_variant,
                cmd_blocks=[],
                force_regenerate=False,
            )
        elif last_exec_cmd and last_exec_cmd in command_ids:
            # We can reuse the snapshot of the current variant
            last_exec_index = command_ids.index(last_exec_cmd)
            return RefStudySearchResult(
                ref_study=curr_variant,
                cmd_blocks=curr_variant.commands[last_exec_index + 1 :],
                force_regenerate=False,
            )

    # We cannot reuse the snapshot of the current variant
    # To generate the last variant of a descendant of variants, we must search for
    # the most recent snapshot in order to use it as a reference study.
    # If no snapshot is found, we use the root study as a reference study.

    snapshot_vars = [v for v in descendants if v.is_snapshot_up_to_date()]

    if snapshot_vars:
        # We use the most recent snapshot as a reference study
        ref_study = max(snapshot_vars, key=lambda v: v.snapshot.created_at)

        # This variant's snapshot corresponds to the commands actually generated
        # at the time of the snapshot. However, we need to retrieve the remaining commands,
        # because the snapshot generation may be incomplete.
        last_exec_cmd = ref_study.snapshot.last_executed_command  # ID of the command
        command_ids = [c.id for c in ref_study.commands]
        if not last_exec_cmd or last_exec_cmd not in command_ids:
            # The last executed command may be missing (probably caused by a bug)
            # or may reference a removed command.
            # This requires regenerating the snapshot from scratch,
            # with all commands from the reference study.
            cmd_blocks = ref_study.commands[:]
        else:
            last_exec_index = command_ids.index(last_exec_cmd)
            cmd_blocks = ref_study.commands[last_exec_index + 1 :]

        # We need to add all commands from the descendants of variants
        # starting at the first descendant of reference study.
        index = descendants.index(ref_study)
        cmd_blocks.extend([c for v in descendants[index + 1 :] for c in v.commands])

    else:
        # We use the root study as a reference study
        ref_study = root_study
        cmd_blocks = [c for v in descendants for c in v.commands]

    return RefStudySearchResult(ref_study=ref_study, cmd_blocks=cmd_blocks, force_regenerate=True)
