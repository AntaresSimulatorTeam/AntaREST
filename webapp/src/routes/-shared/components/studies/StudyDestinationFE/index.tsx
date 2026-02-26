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

import { Box, Typography } from "@mui/material";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { TREE_ROOT_NAME } from "@/components/utils/constants";
import reactHookFormSupport from "@/hoc/reactHookFormSupport";
import { directoryQueries } from "@/queries/directories/queries";

import { validatePath, validateString } from "@/utils/validation/string";
import { combineValidators } from "@/utils/validation/utils";
import DirectoryBreadcrumbs from "./DirectoryBreadcrumbs";
import DirectoryList from "./DirectoryList";
import { containerSx, explorerPanelSx } from "./styles";
import type { BreadcrumbSegment, DirectoryValue } from "./types";
import { buildDirectoryIndex, getDirectChildren, getDirectoryAncestors } from "./utils";

const ROOT_DIRECTORY: DirectoryValue = { id: null, newDirectoryPath: "" };

interface Props {
  /** Current structured value managed by React Hook Form (or parent). */
  value?: DirectoryValue;
  defaultValue?: DirectoryValue;
  onChange?: (event: { target: { value: DirectoryValue } }) => void;
  onBlur?: () => void;
  name?: string;
  disabled?: boolean;
  error?: boolean;
  helperText?: React.ReactNode;
  /** Forwarded to the hidden InputBase inside the address bar (for RHF ref). */
  inputRef?: React.Ref<HTMLInputElement>;
  /** Optional content rendered below the explorer panel (e.g. a checkbox). */
  children?: React.ReactNode;
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
  children,
}: Props) {
  const { data: directories } = useSuspenseQuery(directoryQueries.list());

  const index = useMemo(() => buildDirectoryIndex(directories), [directories]);

  const [selection, setSelection] = useState<DirectoryValue>(() => {
    const initial = value ?? ROOT_DIRECTORY;
    const { id } = initial;

    // Validate the ID and fall back to root when stale / invalid.
    const validId = id !== null && index.has(id) ? id : null;

    return { id: validId, newDirectoryPath: initial.newDirectoryPath };
  });

  const { id: currentDirId, newDirectoryPath } = selection;

  const childDirectories = useMemo(
    () => getDirectChildren(currentDirId, directories),
    [currentDirId, directories],
  );

  const breadcrumbs = useMemo(() => {
    const root: BreadcrumbSegment = { id: null, name: TREE_ROOT_NAME };

    if (!currentDirId) {
      return [{ ...root, active: true }];
    }

    const ancestors = getDirectoryAncestors(currentDirId, index);

    return [
      root,
      ...ancestors.map((directory, index) => ({
        id: directory.id,
        name: directory.name,
        active: index === ancestors.length - 1,
      })),
    ];
  }, [currentDirId, index]);

  const emitChange = (directoryId: string | null, path: string) => {
    onChange?.({ target: { value: { id: directoryId, newDirectoryPath: path } } });
  };

  const navigateTo = (directoryId: string | null) => {
    setSelection((prev) => ({ ...prev, id: directoryId }));
    emitChange(directoryId, newDirectoryPath);
  };

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleGoUp = () => {
    if (currentDirId) {
      navigateTo(index.get(currentDirId)?.parentId ?? null);
    }
  };

  const handleNewPathChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const updated = event.target.value;
    setSelection((prev) => ({ ...prev, newDirectoryPath: updated }));
    emitChange(currentDirId, updated);
  };

  const handleNewPathKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Backspace" && !newDirectoryPath && currentDirId) {
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
          newDirectoryPath={newDirectoryPath}
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

      {children}
    </Box>
  );
}

////////////////////////////////////////////////////////////////
// RHF support
////////////////////////////////////////////////////////////////

const StudyDestinationFEWithReactHookFormSupport = reactHookFormSupport({
  defaultValue: ROOT_DIRECTORY,
  preValidate: (value: DirectoryValue) =>
    combineValidators(
      validatePath({ allowEmpty: true, allowToStartWithSlash: false, allowToEndWithSlash: false }),
      validateString({ specialChars: { chars: "/", mode: "allow" }, allowEmpty: true }),
    )(value.newDirectoryPath),
})(StudyDestinationFE);

export { StudyDestinationFE };
export default StudyDestinationFEWithReactHookFormSupport;
