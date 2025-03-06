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

"""
This module dedicated to variant snapshot generation.
"""

import datetime
import logging
import shutil
from pathlib import Path
from typing import List, NamedTuple, Optional, Sequence, Tuple

from antarest.core.exceptions import VariantGenerationError
from antarest.core.interfaces.cache import (
    ICache,
    study_config_cache_key,
    study_raw_cache_key,
)
from antarest.core.jwt import JWTUser
from antarest.core.model import StudyPermissionType
from antarest.core.tasks.service import ITaskNotifier, NoopNotifier
from antarest.study.model import RawStudy, StudyAdditionalData
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfigDTO
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy, StudyFactory
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.utils import assert_permission_on_studies, export_study_flat, remove_from_cache
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.dbmodel import CommandBlock, VariantStudy, VariantStudySnapshot
from antarest.study.storage.variantstudy.model.model import GenerationResultInfoDTO
from antarest.study.storage.variantstudy.repository import VariantStudyRepository
from antarest.study.storage.variantstudy.variant_command_generator import VariantCommandGenerator

logger = logging.getLogger(__name__)


OUTPUT_RELATIVE_PATH = "output"


class SnapshotGenerator:
    """
    Helper class used to generate snapshots for variant studies.
    """

    def __init__(
        self,
        cache: ICache,
        raw_study_service: RawStudyService,
        command_factory: CommandFactory,
        study_factory: StudyFactory,
        repository: VariantStudyRepository,
    ):
        self.cache = cache
        self.raw_study_service = raw_study_service
        self.command_factory = command_factory
        self.study_factory = study_factory
        self.repository = repository

    def generate_snapshot(
        self,
        variant_study_id: str,
        jwt_user: JWTUser,
        *,
        denormalize: bool = True,
        from_scratch: bool = False,
        notifier: ITaskNotifier = NoopNotifier(),
        listener: Optional[ICommandListener] = None,
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
        assert_permission_on_studies(jwt_user, [root_study, *descendants], StudyPermissionType.READ, raising=True)
        search_result = search_ref_study(root_study, descendants, from_scratch=from_scratch)

        ref_study = search_result.ref_study
        cmd_blocks = search_result.cmd_blocks

        # Get snapshot directory
        variant_study = descendants[-1]
        snapshot_dir = variant_study.snapshot_dir

        try:
            if search_result.force_regenerate or not snapshot_dir.exists():
                self._invalidate_cache(variant_study_id)
                logger.info(f"Exporting the reference study '{ref_study.id}' to '{snapshot_dir.name}'...")
                shutil.rmtree(snapshot_dir, ignore_errors=True)
                self._export_ref_study(snapshot_dir, ref_study)

            # The snapshot is generated, we also need to de-normalize the matrices.
            file_study = self.study_factory.create_from_fs(
                snapshot_dir,
                study_id=variant_study_id,
                output_path=snapshot_dir / OUTPUT_RELATIVE_PATH,
                use_cache=True,
            )
            logger.info(f"Applying commands to the reference study '{ref_study.id}'...")
            results = self._apply_commands(file_study, variant_study, cmd_blocks, listener)
            if denormalize:
                logger.info(f"Denormalizing variant study {variant_study_id}")
                file_study.tree.denormalize()

            # Finally, we can update the database.
            logger.info(f"Saving new snapshot for study {variant_study_id}")
            variant_study.snapshot = VariantStudySnapshot(
                id=variant_study_id,
                created_at=datetime.datetime.utcnow(),
                last_executed_command=(variant_study.commands[-1].id if variant_study.commands else None),
            )

            logger.info(f"Reading additional data from files for study {file_study.config.study_id}")
            variant_study.additional_data = self._read_additional_data(file_study)
            self.repository.save(variant_study)

            self._update_cache(file_study)

        except Exception:
            self._invalidate_cache(variant_study_id)
            shutil.rmtree(snapshot_dir, ignore_errors=True)
            raise

        else:
            try:
                notifier.notify_message(results.model_dump_json())
            except Exception as exc:
                # This exception is ignored, because it is not critical.
                logger.warning(f"Error while sending notification: {exc}", exc_info=True)

        return results

    def _retrieve_descendants(self, variant_study_id: str) -> Tuple[RawStudy, Sequence[VariantStudy]]:
        # Get all ancestors of the current study from bottom to top
        # The first IDs are variant IDs, the last is the root study ID.
        ancestor_ids = self.repository.get_ancestor_or_self_ids(variant_study_id)
        descendant_ids = ancestor_ids[::-1]
        descendants = self.repository.find_variants(descendant_ids)
        root_study = self.repository.one(descendant_ids[0])
        return root_study, descendants

    def _export_ref_study(self, snapshot_dir: Path, ref_study: RawStudy | VariantStudy) -> None:
        if isinstance(ref_study, VariantStudy):
            snapshot_dir.parent.mkdir(parents=True, exist_ok=True)
            export_study_flat(
                ref_study.snapshot_dir,
                snapshot_dir,
                self.study_factory,
                denormalize=False,  # de-normalization is done at the end
                outputs=False,  # do NOT export outputs
            )
        elif isinstance(ref_study, RawStudy):
            self.raw_study_service.export_study_flat(
                ref_study,
                snapshot_dir,
                denormalize=False,  # de-normalization is done at the end
                outputs=False,  # do NOT export outputs
            )
        else:  # pragma: no cover
            raise TypeError(repr(type(ref_study)))

    def _apply_commands(
        self,
        file_study: FileStudy,
        variant_study: VariantStudy,
        cmd_blocks: Sequence[CommandBlock],
        listener: Optional[ICommandListener] = None,
    ) -> GenerationResultInfoDTO:
        commands = [self.command_factory.to_command(cb.to_dto()) for cb in cmd_blocks]
        generator = VariantCommandGenerator(self.study_factory)
        results = generator.generate(
            commands,
            study=file_study,
            metadata=variant_study,
            delete_on_failure=False,
        )
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
        return results

    def _read_additional_data(self, file_study: FileStudy) -> StudyAdditionalData:
        horizon = file_study.tree.get(url=["settings", "generaldata", "general", "horizon"])
        author = file_study.tree.get(url=["study", "antares", "author"])
        assert isinstance(author, str)
        assert isinstance(horizon, (str, int))
        study_additional_data = StudyAdditionalData(horizon=horizon, author=author)
        return study_additional_data

    def _invalidate_cache(self, study_id: str) -> None:
        remove_from_cache(self.cache, study_id)

    def _update_cache(self, file_study: FileStudy) -> None:
        # The study configuration is changed, so we update the cache.
        self.cache.invalidate(study_raw_cache_key(file_study.config.study_id))
        self.cache.put(
            study_config_cache_key(file_study.config.study_id),
            FileStudyTreeConfigDTO.from_build_config(file_study.config).model_dump(),
        )


class RefStudySearchResult(NamedTuple):
    """
    Result of the search for the reference study.
    """

    ref_study: RawStudy | VariantStudy
    cmd_blocks: Sequence[CommandBlock]
    force_regenerate: bool = False


def search_ref_study(
    root_study: RawStudy | VariantStudy,
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
    ref_study: RawStudy | VariantStudy

    # The commands to apply on the reference study to generate the current variant
    cmd_blocks: List[CommandBlock]

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
