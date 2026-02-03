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
import ArrowDownwardIcon from "@mui/icons-material/ArrowDownward";
import ArrowUpwardIcon from "@mui/icons-material/ArrowUpward";
import FolderIcon from "@mui/icons-material/Folder";
import LayersIcon from "@mui/icons-material/Layers";
import LayersClearIcon from "@mui/icons-material/LayersClear";
import RadarIcon from "@mui/icons-material/Radar";
import { IconButton, ToggleButton, ToggleButtonGroup, Tooltip } from "@mui/material";
import { useTranslation } from "react-i18next";
import SelectFE from "@/components/fieldEditors/SelectFE";
import RefreshButton from "@/routes/_authenticated/studies/-components/RefreshButton";
import type { StudiesSortConf } from "@/redux/ducks/studies";

const sortOptions = [
  {
    labelKey: "studies.sortByName",
    value: JSON.stringify({ property: "name", order: "ascend" }),
    icon: ArrowUpwardIcon,
  },
  {
    labelKey: "studies.sortByName",
    value: JSON.stringify({ property: "name", order: "descend" }),
    icon: ArrowDownwardIcon,
  },
  {
    labelKey: "studies.sortByDate",
    value: JSON.stringify({
      property: "modificationDate",
      order: "ascend",
    }),
    icon: ArrowUpwardIcon,
  },
  {
    labelKey: "studies.sortByDate",
    value: JSON.stringify({
      property: "modificationDate",
      order: "descend",
    }),
    icon: ArrowDownwardIcon,
  },
];

interface FilterControlsProps {
  activeTree: "managed" | "external";
  strictPath: boolean;
  isReferenceTypeActive: boolean;
  canScan: boolean;
  sortConf: StudiesSortConf;
  onToggleStrictPath: () => void;
  onToggleStudyType: () => void;
  onScanFolder: () => void;
  onSortChange: (sortConf: StudiesSortConf) => void;
}

function FilterControls({
  activeTree,
  strictPath,
  isReferenceTypeActive,
  canScan,
  sortConf,
  onToggleStrictPath,
  onToggleStudyType,
  onScanFolder,
  onSortChange,
}: FilterControlsProps) {
  const { t } = useTranslation();

  return (
    <>
      {/* Folder hierarchy toggle - only for external tree */}
      {activeTree === "external" && (
        <>
          <ToggleButtonGroup
            value={strictPath}
            exclusive
            onChange={onToggleStrictPath}
            size="extra-small"
            color="primary"
          >
            <Tooltip title={t("studies.filters.strictfolder")}>
              <ToggleButton value={true}>
                <FolderIcon />
              </ToggleButton>
            </Tooltip>
            <Tooltip title={t("studies.filters.showChildrens")}>
              <ToggleButton value={false}>
                <AccountTreeIcon />
              </ToggleButton>
            </Tooltip>
          </ToggleButtonGroup>

          {/* Folder scan button - only for desktop mode enabled */}
          {canScan && (
            <Tooltip title={t("studies.scanFolder")}>
              <IconButton onClick={onScanFolder}>
                <RadarIcon />
              </IconButton>
            </Tooltip>
          )}
        </>
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
        value={JSON.stringify(sortConf)}
        onChange={(event) => onSortChange(JSON.parse(event.target.value as string))}
        options={sortOptions.map(({ labelKey, ...rest }) => ({
          label: t(labelKey),
          ...rest,
        }))}
        sx={{ minWidth: 90 }}
        margin="dense"
      />
    </>
  );
}

export default FilterControls;
