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
import type { ViewMode } from "../types";

/**
 * Props shared between GridStudyCard and ListStudyCard.
 * Both layouts receive the same data and handlers from the smart StudyCard coordinator.
 * They never reach into Redux or perform side effects directly.
 */
export interface StudyCardLayoutProps {
  study: StudyMetadata;
  directoryPath: string | null;
  width: number;
  height: number;
  isSelected: boolean;
  hasStudiesSelected: boolean;
  onOpen: () => void;
  onDirectoryClick: () => void;
  onCopyId: () => void;
  onSelectionChange: () => void;
  onMenuOpen: (event: React.MouseEvent<HTMLButtonElement>) => void;
}

/**
 * Shared item data passed to every cell via react-window's `itemData` prop.
 * Extracted here so `StudyCardCellProps` and callers can reference it by name
 * rather than navigating through `GridChildComponentProps<...>["data"]`.
 */
export interface StudyCellData {
  columnCount: number;
  columnWidth: number;
  rowHeight: number;
  studyIds: Array<StudyMetadata["id"]>;
  selectedStudyIds: Array<StudyMetadata["id"]>;
  toggleStudySelection: (id: StudyMetadata["id"]) => void;
  viewMode: ViewMode;
  directories: Directory[];
}
