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

import AccountTreeIcon from "@mui/icons-material/AccountTree";
import FolderIcon from "@mui/icons-material/Folder";
import LayersIcon from "@mui/icons-material/Layers";
import LayersClearIcon from "@mui/icons-material/LayersClear";
import RadarIcon from "@mui/icons-material/Radar";
import ViewListIcon from "@mui/icons-material/ViewList";
import ViewModuleIcon from "@mui/icons-material/ViewModule";
import { IconButton, ToggleButton, ToggleButtonGroup, Tooltip } from "@mui/material";
import { useTranslation } from "react-i18next";
import SelectFE from "@/components/fieldEditors/SelectFE";
import RefreshButton from "@/routes/_authenticated/studies/-components/RefreshButton";
import {
  findStudySortOptionId,
  getStudySortOption,
  STUDY_SORT_OPTIONS,
  type StudySortOptionId,
  toStudySortConfig,
} from "@/routes/_authenticated/studies/-components/StudiesList/Header/studySortUtils";
import type { StudySortConfig } from "@/types/types";
import type { ViewMode } from "../types";

interface FilterControlsProps {
  showDescendants: boolean;
  isExternalRoot: boolean;
  isReferenceTypeActive: boolean;
  canScan: boolean;
  sortConfig: StudySortConfig;
  viewMode: ViewMode;
  onToggleShowDescendants: (value: boolean) => void;
  onToggleStudyType: () => void;
  onScanDirectory: () => void;
  onSortChange: (sortConfig: StudySortConfig) => void;
  onViewModeChange: (mode: ViewMode) => void;
}

function FilterControls({
  showDescendants,
  isExternalRoot,
  isReferenceTypeActive,
  canScan,
  sortConfig,
  viewMode,
  onToggleShowDescendants,
  onToggleStudyType,
  onScanDirectory,
  onSortChange,
  onViewModeChange,
}: FilterControlsProps) {
  const { t } = useTranslation();

  const handleSortChange = (id: StudySortOptionId) => {
    onSortChange(toStudySortConfig(getStudySortOption(id)));
  };

  return (
    <>
      {/* Directory hierarchy toggle - current dir only vs include descendants (hidden for external root) */}
      {!isExternalRoot && (
        <ToggleButtonGroup
          value={showDescendants}
          exclusive
          onChange={(_e, v) => v !== null && onToggleShowDescendants(v)}
          size="extra-small"
          color="primary"
        >
          <Tooltip title={t("studies.filters.noDescendants")}>
            <ToggleButton value={false}>
              <FolderIcon />
            </ToggleButton>
          </Tooltip>
          <Tooltip title={t("studies.filters.showDescendants")}>
            <ToggleButton value={true}>
              <AccountTreeIcon />
            </ToggleButton>
          </Tooltip>
        </ToggleButtonGroup>
      )}

      {/* View mode toggle */}
      <ToggleButtonGroup
        value={viewMode}
        exclusive
        onChange={(_e, v) => v !== null && onViewModeChange(v)}
        size="extra-small"
        color="primary"
      >
        <Tooltip title={t("studies.viewMode.grid")}>
          <ToggleButton value="grid">
            <ViewModuleIcon />
          </ToggleButton>
        </Tooltip>
        <Tooltip title={t("studies.viewMode.list")}>
          <ToggleButton value="list">
            <ViewListIcon />
          </ToggleButton>
        </Tooltip>
      </ToggleButtonGroup>

      {/* Directory scan button - only for desktop mode enabled */}
      {canScan && (
        <Tooltip title={t("studies.scanFolder")}>
          <IconButton onClick={onScanDirectory}>
            <RadarIcon />
          </IconButton>
        </Tooltip>
      )}

      {/* Study type filter (references vs all) */}
      <Tooltip
        title={
          isReferenceTypeActive
            ? t("studies.filters.disableReferenceType")
            : t("studies.filters.enableReferenceType")
        }
      >
        <IconButton onClick={onToggleStudyType}>
          {isReferenceTypeActive ? <LayersClearIcon /> : <LayersIcon />}
        </IconButton>
      </Tooltip>

      {/* Refresh button */}
      <RefreshButton mini />

      {/* Sort selector */}
      <SelectFE
        size="extra-small"
        label={t("studies.sortBy")}
        value={findStudySortOptionId(sortConfig)}
        onChange={(event) => handleSortChange(event.target.value as StudySortOptionId)}
        options={STUDY_SORT_OPTIONS.map(({ id, labelKey, icon }) => ({
          value: id,
          label: t(labelKey),
          icon,
        }))}
        sx={{ minWidth: 90 }}
        margin="dense"
      />
    </>
  );
}

export default FilterControls;
