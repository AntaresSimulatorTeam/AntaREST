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

import type { Directory } from "@/services/api/directories/types";
import type { StudyMetadata } from "@/types/types";
import StudyActionsMenu from "../../../../../-shared/components/studies/StudyActionsMenu";
import type { ViewMode } from "../types";
import { useStudyCard } from "./useStudyCard";
import GridStudyCard from "./GridStudyCard";
import ListStudyCard from "./ListStudyCard";

interface Props {
  id: StudyMetadata["id"];
  width: number;
  height: number;
  isSelected: boolean;
  hasStudiesSelected: boolean;
  toggleStudySelection: (id: StudyMetadata["id"]) => void;
  viewMode: ViewMode;
  directories: Directory[];
}

function StudyCard({
  id,
  width,
  height,
  isSelected,
  hasStudiesSelected,
  toggleStudySelection,
  viewMode,
  directories,
}: Props) {
  const {
    study,
    directoryPath,
    anchorEl,
    onOpen,
    onDirectoryClick,
    onCopyId,
    onSelectionChange,
    onMenuOpen,
    onMenuClose,
  } = useStudyCard(id, directories, toggleStudySelection);

  if (!study) {
    return null;
  }

  const layoutProps = {
    study,
    directoryPath,
    width,
    height,
    isSelected,
    hasStudiesSelected,
    onOpen,
    onDirectoryClick,
    onCopyId,
    onSelectionChange,
    onMenuOpen,
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      {viewMode === "list" ? (
        <ListStudyCard {...layoutProps} />
      ) : (
        <GridStudyCard {...layoutProps} />
      )}
      <StudyActionsMenu open={!!anchorEl} anchorEl={anchorEl} onClose={onMenuClose} study={study} />
    </>
  );
}

export default StudyCard;
