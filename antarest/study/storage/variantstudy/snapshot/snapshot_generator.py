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
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, NamedTuple

from antarest.core.exceptions import (
    ShouldNotHappenException,
    UnsupportedOperationOnArchivedStudy,
    VariantGenerationError,
)
from antarest.core.tasks.service import ITaskNotifier, NoopNotifier
from antarest.core.utils.collection_utils import index_or_none
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.dao.api.study_factory_dao import StudyFactoryDao
from antarest.study.model import RawStudy, Study, StudyMetadataUpdate
from antarest.study.storage.utils import (
    format_timestamp,
    remove_from_cache,
)
from antarest.study.storage.variantstudy.model.dbmodel import (
    CommandBlock,
    LineageVersions,
    VariantStudy,
    VariantStudySnapshot,
)
from antarest.study.storage.variantstudy.model.model import GenerationResultInfoDTO
from antarest.study.storage.variantstudy.variant_command_generator import apply_commands_to_variant

if TYPE_CHECKING:
    from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VariantLineage:
    root_study: RawStudy
    descendants: list[VariantStudy]

    @property
    def leaf_study(self) -> RawStudy | VariantStudy:
        return self.descendants[-1] if self.descendants else self.root_study

    def get_parent_lineage(self) -> "VariantLineage | None":
        if not self.descendants:
            return None
        return VariantLineage(root_study=self.root_study, descendants=self.descendants[:-1])

    def get_lineage_versions(self) -> LineageVersions:
        return LineageVersions(versions=[(v.id, v.commands_version.version) for v in self.descendants])

    def get_leaf_snapshot_status(self) -> Literal["absent", "unchanged", "parents_changed", "leaf_changed"]:
        """
        The snapshot of the leaf can be in either of 4 status:
         - it does not exist
         - it exists and is consistent with the current versions of studies
         - it exists but some of the parents have changed since its generation
         - it exists and only the leaf itself has changed since its generation
        """
        leaf = self.leaf_study
        if isinstance(leaf, RawStudy):
            return "unchanged"
        snapshot = leaf.snapshot
        if snapshot is None:
            return "absent"
        snapshot_versions = snapshot.lineage_versions
        current_versions = self.get_lineage_versions()
        if snapshot_versions.is_up_to_date_with(current_versions):
            return "unchanged"
        elif snapshot_versions.get_parent_lineage_versions().is_up_to_date_with(
            current_versions.get_parent_lineage_versions()
        ):
            return "leaf_changed"
        else:
            return "parents_changed"

    def get_commands_from(self, study: RawStudy | VariantStudy) -> list[CommandBlock]:
        if study is self.root_study:
            return _aggregate_command_blocks(self.descendants)
        elif isinstance(study, VariantStudy):
            idx = self.descendants.index(study)
            return _aggregate_command_blocks(self.descendants[idx + 1 :])
        raise ValueError(f"Study {study.id} is not part of this lineage")


class RefStudySearchResult(NamedTuple):
    """
    Result of the search for the reference study.
    """

    ref_study: Study
    cmd_blocks: list[CommandBlock]
    force_regenerate: bool = False


def _aggregate_command_blocks(variants: Sequence[VariantStudy]) -> list[CommandBlock]:
    return [cmd for variant in variants for cmd in variant.commands]


def _is_snapshot_up_to_date(lineage: Sequence[VariantStudy]) -> bool:
    """
    Checks if the snapshot of the given variant is up to date with the given variants.
    """
    variant = lineage[-1]
    if variant.snapshot is None:
        return False
    current_lineage_versions = get_lineage_versions(lineage)
    return variant.snapshot.lineage_versions.is_up_to_date_with(current_lineage_versions)


def _has_snapshot_up_to_date_with_parents(lineage: Sequence[VariantStudy]) -> bool:
    current_variant = lineage[-1]
    if current_variant.snapshot is None:
        return False
    current_lineage_versions = get_lineage_versions(lineage)
    return current_variant.snapshot.lineage_versions.versions[:-1] == current_lineage_versions.versions[:-1]


def _find_last_snapshot_up_to_date(
    lineage: VariantLineage,
) -> tuple[Study, list[CommandBlock]]:
    """
    Finds the most recent study up to date.

    It also returns the list of commands to apply in order (from the oldest to the most recent command).
    """
    current_lineage = lineage
    while parent_lineage := current_lineage.get_parent_lineage():
        current_lineage = parent_lineage
        if current_lineage.get_leaf_snapshot_status() == "unchanged":
            return current_lineage.leaf_study, lineage.get_commands_from(current_lineage.leaf_study)
    return lineage.root_study, lineage.get_commands_from(lineage.root_study)


def get_lineage_versions(lineage: Sequence[VariantStudy]) -> LineageVersions:
    return LineageVersions(versions=[(v.id, v.commands_version.version) for v in lineage])


def get_ref_study_snapshot_id(ref_study: Study) -> LineageVersions:
    match ref_study:
        case VariantStudy():
            if snapshot := ref_study.snapshot:
                return snapshot.lineage_versions
            raise ShouldNotHappenException("Snapshot of reference study does not exist.")
        case RawStudy():
            # TODO: for now raw study data is not versioned
            return LineageVersions([])
        case _:
            raise ValueError(f"Unsupported study type: {type(ref_study)}")


class RefStudyChanged(Exception):
    pass


class SnapshotGenerator:
    """
    Generates snapshots for variant studies.
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
        """
        Important notes about concurrent modifications management:

         - since we are making changes to the underlying study, a lock is needed.
           The locking is currently done in the `VariantStudyService.generate` function
           when starting the generation, through a file lock.

        Implementation guarantees safety against concurrent modifications of variant parents by:

        - tagging the generated snapshot with the versions of parent studies, so that we know exactly for what
          commands that snapshot has been generated. If some commands are modified during that generation, they will
          be taken into account in the next one.
        - reading all parents commands and their versions in **one** query, so that we are sure we get a consistent
          view accross all parents.
        - checking, after copy of the reference study, that its version has not changed during the copy
        - invalidating the snapshot at the start of the generation: in case of crash during the generation,
          this ensures we don't keep an incomplete snapshot as valid.

        BUT, the implementation still does not handle correctly concurrent modifications of the root study:
        Because raw studies are not versioned, their version is not tracked in the snapshot versioning.
        A concurrent modification of the root study can lead to a snapshot identified as up-to-date but not
        consistent with that data.

        TODO: In order to fix this, root studies should either be made immutable or versioned.
        """
        logger.info(f"Generating variant study snapshot for '{variant_study_id}'")

        # Note: we don't check any more for READ permissions on the lineage here.
        #       Permissions are only considered at variant creation time, not every time
        #       the snapshot is generated.
        root_study, descendants = self.repository.get_study_lineage(variant_study_id)
        lineage = VariantLineage(root_study, descendants)
        if root_study.archived:
            raise UnsupportedOperationOnArchivedStudy(root_study.id)
        search_result = self.search_ref_study(lineage, from_scratch=from_scratch)

        ref_study = search_result.ref_study
        cmd_blocks = search_result.cmd_blocks

        # Get snapshot directory
        variant_study = descendants[-1]

        new_snapshot_version = get_lineage_versions(descendants)
        try:
            # we need to invalidate the current snapshot, since we start to modify the underlying data.
            # if the process crashes during generation, the snapshot will be invalid and will be regenerated on the next request.
            self.variant_study_service.invalidate_snapshot(variant_study)

            if search_result.force_regenerate:
                initial_ref_versions = get_ref_study_snapshot_id(ref_study)
                self.variant_study_service.create_snapshot(ref_study, variant_study)
                # we need to make sure the ref_study has not changed in the meantime, otherwise we may have copied
                # data that do not correspond to the lineage used for generation
                if isinstance(ref_study, VariantStudy):
                    refreshed_snaphot = self.repository.get_refreshed_snapshot(ref_study.id)
                    final_ref_versions = refreshed_snaphot.lineage_versions if refreshed_snaphot else None
                else:
                    final_ref_versions = LineageVersions([])
                if final_ref_versions != initial_ref_versions:
                    raise RefStudyChanged()

            # The snapshot is generated, we also need to de-normalize the matrices.
            study_dao = dao_factory.get_study_dao(variant_study.id, True)

            logger.info(f"Applying commands to the reference study '{ref_study.id}'...")
            results = self._apply_commands(study_dao, variant_study, cmd_blocks)

            # Finally, we can update the database.
            logger.info(f"Saving new snapshot for study {variant_study_id}")
            last_executed_command = None
            if cmd_blocks:
                last_executed_command = cmd_blocks[-1].id
            elif variant_study.snapshot:
                last_executed_command = variant_study.snapshot.last_executed_command
            variant_study.snapshot = VariantStudySnapshot(
                id=variant_study_id, last_executed_command=last_executed_command, lineage_versions=new_snapshot_version
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

    def search_ref_study(self, lineage: VariantLineage, *, from_scratch: bool) -> RefStudySearchResult:
        """
        Search for the reference study and the commands to use for snapshot generation.

        Args:
            root_study: The root study from which the descendants of variants are derived.
            descendants: The list of descendants of variants from top to bottom.
            from_scratch: Whether to generate the snapshot from scratch or not.

        Returns:
            The reference study and the commands to use for snapshot generation.
        """

        if from_scratch:
            # In the case of a from scratch generation, the root study will be used as the reference study.
            # We need to retrieve all commands from the descendants of variants to apply them on the reference study.
            return RefStudySearchResult(
                ref_study=lineage.root_study,
                cmd_blocks=lineage.get_commands_from(lineage.root_study),
                force_regenerate=True,
            )

        # 1st case: The variant snapshot is already up to date -> No-op.
        # This is handled via the `variant_study_service` before calling the SnapshotGenerator, so we should not bother.
        # And even if it was the case, the 2nd case will handle it.
        # This way we avoid making unnecessary DB queries.

        # 2nd case: The variant has a snapshot, but it is not up to date.
        # We only have to check if we can reuse the snapshot to minimize the generation time.
        # We can reuse the snapshot if the last executed command is still present in the variant commands list.
        # It's not always the case as the user could have removed a command or replaced them all.
        snapshot_status = lineage.get_leaf_snapshot_status()
        match snapshot_status:
            case "absent", "parents_changed":  # we need to re-create the snapshot from parent studies in either case
                ref_study, commands = _find_last_snapshot_up_to_date(lineage)
                return RefStudySearchResult(ref_study=ref_study, cmd_blocks=commands, force_regenerate=True)

            case "leaf_changed", "unchanged":
                study = lineage.leaf_study
                assert isinstance(study, VariantStudy) and study.snapshot is not None

                if study.snapshot.last_executed_command is None:  # Snapshot was generated for empty list of commands
                    return RefStudySearchResult(ref_study=study, cmd_blocks=study.commands, force_regenerate=False)

                command_ids = [c.id for c in study.commands]
                last_cmd_idx = index_or_none(command_ids, study.snapshot.last_executed_command)
                if last_cmd_idx is None:
                    # Fall back to regeneration from ancestors
                    ref_study, commands = _find_last_snapshot_up_to_date(lineage)
                    return RefStudySearchResult(ref_study=ref_study, cmd_blocks=commands, force_regenerate=True)
                else:
                    return RefStudySearchResult(
                        ref_study=study, cmd_blocks=study.commands[last_cmd_idx + 1 :], force_regenerate=False
                    )

        raise ShouldNotHappenException()
        # Final case: The variant has no snapshot, or its `last_executed_command` does not exist anymore.
        # We search for a variant with an up-to-date snapshot to use it as a reference study.
        # If no such variant is found, we use the root study as a reference study.
