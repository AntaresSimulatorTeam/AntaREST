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

import { TREE_ROOT_NAME } from "@/components/utils/constants";
import reactHookFormSupport from "@/hoc/reactHookFormSupport";
import { directoryQueries } from "@/queries/directories/queries";
import { Box, Typography } from "@mui/material";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import type { Directory } from "@/services/api/directories/types";
import { validatePath, validateString } from "@/utils/validation/string";
import { combineValidators } from "@/utils/validation/utils";
import DirectoryBreadcrumbs from "./DirectoryBreadcrumbs";
import DirectoryList from "./DirectoryList";
import { containerSx, explorerPanelSx } from "./styles";
import type { BreadcrumbSegment, DirectoryDestination } from "./types";
import { getDirectChildren, getDirectoryAncestors, mapDirectoriesById } from "./utils";

const ROOT_DIRECTORY: DirectoryDestination = { directoryId: null, newSubdirectoriesPath: "" };

interface Props {
  /** Current structured value managed by React Hook Form (or parent). */
  value?: DirectoryDestination;
  defaultValue?: DirectoryDestination;
  onChange?: (event: { target: { value: DirectoryDestination } }) => void;
  onBlur?: () => void;
  name?: string;
  disabled?: boolean;
  error?: boolean;
  helperText?: React.ReactNode;
  /** Forwarded to the hidden InputBase inside the address bar (for RHF ref). */
  inputRef?: React.Ref<HTMLInputElement>;
}

function selectDirectories(directories: Directory[]) {
  return { directories, directoriesById: mapDirectoriesById(directories) };
}

function StudyDestinationFE({
  value,
  onChange,
  onBlur,
  name,
  disabled = false,
  error = false,
  helperText,
  inputRef,
}: Props) {
  const {
    data: { directories, directoriesById },
  } = useSuspenseQuery({
    ...directoryQueries.list(),
    select: selectDirectories,
  });

  const [selection, setSelection] = useState<DirectoryDestination>(() => {
    const initial = value ?? ROOT_DIRECTORY;
    const { directoryId } = initial;

    // Validate the ID and fall back to root when stale / invalid.
    const validId = directoryId !== null && directoriesById.has(directoryId) ? directoryId : null;

    return { directoryId: validId, newSubdirectoriesPath: initial.newSubdirectoriesPath };
  });

  const { directoryId: currentDirId, newSubdirectoriesPath } = selection;

  const childDirectories = useMemo(
    () => getDirectChildren(currentDirId, directories),
    [currentDirId, directories],
  );

  const breadcrumbs = useMemo(() => {
    const root: BreadcrumbSegment = { id: null, name: TREE_ROOT_NAME };

    if (!currentDirId) {
      return [{ ...root, active: true }];
    }

    const ancestors = getDirectoryAncestors(currentDirId, directoriesById);

    return [
      root,
      ...ancestors.map((directory, index) => ({
        id: directory.id,
        name: directory.name,
        active: index === ancestors.length - 1,
      })),
    ];
  }, [currentDirId, directoriesById]);

  const emitChange = (directoryId: string | null, path: string) => {
    onChange?.({ target: { value: { directoryId, newSubdirectoriesPath: path } } });
  };

  const navigateTo = (directoryId: string | null) => {
    setSelection((prev) => ({ ...prev, directoryId }));
    emitChange(directoryId, newSubdirectoriesPath);
  };

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleGoUp = () => {
    if (currentDirId) {
      navigateTo(directoriesById.get(currentDirId)?.parentId ?? null);
    }
  };

  const handleNewPathChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const updated = event.target.value;
    setSelection((prev) => ({ ...prev, newSubdirectoriesPath: updated }));
    emitChange(currentDirId, updated);
  };

  const handleNewPathKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Backspace" && !newSubdirectoriesPath && currentDirId) {
      event.preventDefault();
      handleGoUp();
    }
  };

  // Only fires onBlur (for RHF "touched" tracking) when focus truly leaves
  // the entire component, not when it moves between internal elements.
  const handleContainerBlur = (event: React.FocusEvent) => {
    if (!event.currentTarget.contains(event.relatedTarget as Node | null)) {
      onBlur?.();
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box sx={containerSx} onBlur={handleContainerBlur}>
      <Box sx={explorerPanelSx(error)}>
        <DirectoryBreadcrumbs
          breadcrumbs={breadcrumbs}
          newSubdirectoriesPath={newSubdirectoriesPath}
          disabled={disabled}
          canGoUp={currentDirId !== null}
          inputRef={inputRef}
          name={name}
          onGoUp={handleGoUp}
          onBreadcrumbClick={(segment) => navigateTo(segment.id)}
          onNewPathChange={handleNewPathChange}
          onNewPathKeyDown={handleNewPathKeyDown}
        />

        <DirectoryList
          childDirectories={childDirectories}
          allDirectories={directories}
          onDirectoryClick={(directory) => navigateTo(directory.id)}
        />
      </Box>

      {helperText && (
        <Typography variant="caption" color={error ? "error.main" : "text.secondary"}>
          {helperText}
        </Typography>
      )}
    </Box>
  );
}

////////////////////////////////////////////////////////////////
// RHF support
////////////////////////////////////////////////////////////////

const StudyDestinationFEWithReactHookFormSupport = reactHookFormSupport({
  defaultValue: ROOT_DIRECTORY,
  preValidate: (value: DirectoryDestination) =>
    combineValidators(
      validatePath({ allowEmpty: true, allowToStartWithSlash: false, allowToEndWithSlash: false }),
      validateString({
        allowEmpty: true,
        allowSpaces: true,
        specialChars: { chars: "_-/", mode: "allow" },
      }),
    )(value.newSubdirectoriesPath),
})(StudyDestinationFE);

export { StudyDestinationFE };
export default StudyDestinationFEWithReactHookFormSupport;
