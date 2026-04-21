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

import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import { updateStudyFilters } from "@/redux/ducks/studies";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getStudy } from "@/redux/selectors";
import { getDescendantIds } from "@/routes/_authenticated/studies/-components/StudyTree/ManagedTree/utils";
import type { Directory } from "@/services/api/directories/types";
import type { StudyMetadata } from "@/types/types";
import { toError } from "@/utils/fnUtils";
import { useNavigate } from "@tanstack/react-router";
import debug from "debug";
import { useSnackbar } from "notistack";
import { useState } from "react";
import { useTranslation } from "react-i18next";

const logError = debug("antares:studieslist:error");

////////////////////////////////////////////////////////////////
// Utils
////////////////////////////////////////////////////////////////

function getStudyDirectoryPath(study: StudyMetadata, directories: Directory[]): string | null {
  if (study.managed) {
    const directoryById = new Map(directories.map((directory) => [directory.id, directory]));

    const collectAncestorNames = (directoryId: string | null): string[] => {
      const directory = directoryId ? directoryById.get(directoryId) : undefined;
      return directory ? [...collectAncestorNames(directory.parentId), directory.name] : [];
    };

    return collectAncestorNames(study.directoryId ?? null).join("/") || null;
  }

  // External: /${workspace}/...path matches tree item IDs used for navigation.
  const pathSegments = study.folder?.split("/").filter(Boolean).slice(0, -1) ?? [];
  return ["", study.workspace, ...pathSegments].join("/");
}

////////////////////////////////////////////////////////////////
// Hook
////////////////////////////////////////////////////////////////

export interface UseStudyCardResult {
  study: StudyMetadata | undefined;
  directoryPath: string | null;
  anchorEl: HTMLElement | null;
  onOpen: () => void;
  onDirectoryClick: () => void;
  onCopyId: () => void;
  onSelectionChange: () => void;
  onMenuOpen: (event: React.MouseEvent<HTMLButtonElement>) => void;
  onMenuClose: () => void;
}

/**
 * Encapsulates all data-fetching, navigation, Redux dispatch, and event handlers
 * for a study card. Layout components (Grid/List) stay free of these concerns.
 *
 * @param id - The unique identifier of the study to display.
 * @param directories - The list of all available directories, used to resolve the display directory path.
 * @param toggleStudySelection - Callback to toggle the selection state of the study by its id.
 * @returns An object containing the study data, computed display directory, menu anchor state, and all event handlers needed by the study card.
 */
export function useStudyCard(
  id: StudyMetadata["id"],
  directories: Directory[],
  toggleStudySelection: (id: StudyMetadata["id"]) => void,
): UseStudyCardResult {
  const { t } = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const study = useAppSelector((state) => getStudy(state, id));
  const navigate = useNavigate();
  const dispatch = useAppDispatch();

  const directoryPath = study ? getStudyDirectoryPath(study, directories) : null;

  const onOpen = () => {
    if (!study) {
      return;
    }
    navigate({ to: "/studies/$studyId", params: { studyId: study.id } });
  };

  const onDirectoryClick = () => {
    if (!study) {
      return;
    }

    if (study.managed) {
      const directoryId = study.directoryId ?? null;
      dispatch(
        updateStudyFilters({
          activeTree: "managed",
          managed: {
            directoryId,
            directoryIds: directoryId ? getDescendantIds(directoryId, directories) : null,
            collapsed: false,
          },
        }),
      );
    } else {
      dispatch(
        updateStudyFilters({
          activeTree: "external",
          external: { path: directoryPath ?? "", collapsed: false },
        }),
      );
    }
  };

  const onCopyId = () => {
    navigator.clipboard
      .writeText(id)
      .then(() => {
        enqueueSnackbar(t("study.success.studyIdCopy"), { variant: "success" });
      })
      .catch((err) => {
        enqueueErrorSnackbar(t("study.error.studyIdCopy"), toError(err));
        logError("Failed to copy study id", id, err);
      });
  };

  const onSelectionChange = () => {
    toggleStudySelection(id);
  };

  const onMenuOpen = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const onMenuClose = () => {
    setAnchorEl(null);
  };

  return {
    study,
    directoryPath,
    anchorEl,
    onOpen,
    onDirectoryClick,
    onCopyId,
    onSelectionChange,
    onMenuOpen,
    onMenuClose,
  };
}
