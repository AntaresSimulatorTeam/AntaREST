/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import { z } from "zod";
import type { Directory } from "@/services/api/directories/types";
import type { StudyMetadata } from "@/types/types";
import type { MoveResult } from ".";

export { toDirectoryPath } from "../../StudyDestinationFE/utils";

////////////////////////////////////////////////////////////////
// Schema
////////////////////////////////////////////////////////////////

const directoryValueSchema = z.object({
  id: z.string().nullable(),
  newDirectoryPath: z.string().transform((v) => v.trim().split("/").filter(Boolean).join("/")),
});

export const formSchema = z.object({
  directory: directoryValueSchema,
  redirect: z.boolean(),
});

export type FormValues = z.input<typeof formSchema>;

////////////////////////////////////////////////////////////////
// Utils
////////////////////////////////////////////////////////////////

/**
 * Derives the initial directory ID from the studies being moved.
 *
 * - If all studies share the same directory, the explorer opens there.
 * - Otherwise (mixed directories), it opens at root.
 *
 * @param studies - The studies being moved.
 * @returns The shared directory ID, or `null` for root.
 */
export function getInitialDirectoryId(studies: StudyMetadata[]): string | null {
  if (studies.length === 0) {
    return null;
  }

  const firstDirId = studies[0].directoryId ?? null;

  if (studies.every((study) => (study.directoryId ?? null) === firstDirId)) {
    return firstDirId;
  }

  return null;
}

/**
 * Whether the submit button should be enabled even when the form is pristine.
 *
 * Returns `true` only when the explorer starts at root AND at least one study
 * is not already at root. This prevents no-op moves while still allowing
 * bulk actions that consolidate studies from different directories into root.
 *
 * @param initialDirectoryId - The initial directory ID from {@link getInitialDirectoryId}.
 * @param studies - The studies being moved.
 * @returns Whether submitting without changes should be allowed.
 */
export function computeAllowSubmitOnPristine(
  initialDirectoryId: string | null,
  studies: StudyMetadata[],
) {
  if (initialDirectoryId !== null) {
    return false;
  }

  return studies.some((study) => study.directoryId !== null && study.directoryId !== undefined);
}

/**
 * Resolves the final directory ID for the redirect after a successful move.
 *
 * When the user typed a new sub-directory name, this walks the freshly-fetched
 * directory tree to find the deepest directory that was created.
 * Otherwise the selected directory ID is returned as-is.
 *
 * @param directory - Parsed directory value from the form.
 * @param directories - Freshly-fetched directory list (includes newly created dirs).
 * @returns The directory ID to redirect to, or `null` for root.
 */
export function resolveRedirectDirectoryId(
  directory: MoveResult["directory"],
  directories: Directory[],
): string | null {
  if (!directory.newDirectoryPath) {
    return directory.id;
  }

  const segments = directory.newDirectoryPath.split("/").filter(Boolean);
  let currentId = directory.id;

  for (const segment of segments) {
    const child = directories.find(
      (directory) => directory.parentId === currentId && directory.name === segment,
    );

    if (!child) {
      break;
    }

    currentId = child.id;
  }

  return currentId;
}
