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

import CustomScrollbar from "@/components/CustomScrollbar";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import { directoryQueries } from "@/queries/directories/queries";
import { updateStudyFilters, updateStudySortConfig } from "@/redux/ducks/studies";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getStudyFilters, getStudySortConfig } from "@/redux/selectors";
import { getDescendantIds } from "@/routes/_authenticated/studies/-components/StudyTree/ManagedTree/utils";
import type { Study } from "@/services/api/studies/types";
import { scanFolder } from "@/services/api/study";
import type { StudySortConfig } from "@/types/types";
import { toError } from "@/utils/fnUtils";
import { Box } from "@mui/material";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { ViewMode } from "../types";
import BatchActions from "./BatchActions";
import FilterControls from "./FilterControls";
import { useBreadcrumbs } from "./hooks/useBreadcrumbs";
import NavigationBreadcrumbs from "./NavigationBreadcrumbs";
import ScanDirectoryDialog from "./ScanDirectoryDialog";
import type { BreadcrumbItem } from "./types";

export interface Props {
  studyIds: Array<Study["id"]>;
  selectedStudyIds: Array<Study["id"]>;
  setSelectedStudyIds: (ids: Array<Study["id"]>) => void;
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
}

function Header({
  studyIds,
  selectedStudyIds,
  setSelectedStudyIds,
  viewMode,
  onViewModeChange,
}: Props) {
  const dispatch = useAppDispatch();
  const { t } = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  // Redux state
  const filters = useAppSelector(getStudyFilters);
  const { activeTree, managed, external } = filters;
  const sortConfig = useAppSelector(getStudySortConfig);

  // Local state
  const [confirmDirectoryScan, setConfirmDirectoryScan] = useState(false);
  const [isRecursiveScan, setIsRecursiveScan] = useState(false);

  const isDesktopMode = import.meta.env.MODE === "desktop";
  const isReferenceStudyTypeActive = filters.type === "references";
  const canScan = activeTree === "external" && external.path !== "";
  const showDescendants =
    activeTree === "external" ? external.showDescendants : managed.showDescendants;
  const isExternalRoot = activeTree === "external" && external.path === "";

  const { data: directories } = useSuspenseQuery(directoryQueries.list());

  // Breadcrumb navigation
  const breadcrumbItems = useBreadcrumbs({
    activeTree,
    managedDirectoryId: managed.directoryId,
    externalPath: external.path,
    directories,
  });

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleNavigate = (item: BreadcrumbItem) => {
    if (activeTree === "managed") {
      dispatch(
        updateStudyFilters({
          activeTree: "managed",
          managed: {
            directoryId: item.id,
            directoryIds: item.id ? getDescendantIds(item.id, directories) : null,
          },
        }),
      );
    } else {
      dispatch(
        updateStudyFilters({
          activeTree: "external",
          external: { path: item.path ?? "" },
        }),
      );
    }
  };

  const handleToggleShowDescendants = (value: boolean) => {
    if (activeTree === "external") {
      dispatch(updateStudyFilters({ external: { showDescendants: value } }));
    } else {
      dispatch(updateStudyFilters({ managed: { showDescendants: value } }));
    }
  };

  const handleToggleStudyType = () => {
    dispatch(updateStudyFilters({ type: isReferenceStudyTypeActive ? "all" : "references" }));
  };

  const handleSortChange = (config: StudySortConfig) => {
    dispatch(updateStudySortConfig(config));
  };

  const handleOpenScanDialog = () => {
    setConfirmDirectoryScan(true);
  };

  const handleCloseScanDialog = () => {
    setConfirmDirectoryScan(false);
    setIsRecursiveScan(false);
  };

  const handleConfirmScan = async () => {
    try {
      if (activeTree === "external" && external.path) {
        await scanFolder(external.path, isRecursiveScan);
      }

      handleCloseScanDialog();
    } catch (err) {
      enqueueErrorSnackbar(t("studies.error.scanFolder"), toError(err));
    }
  };

  const handleToggleRecursiveScan = () => {
    setIsRecursiveScan((prev) => !prev);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <CustomScrollbar>
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 1,
            px: 2,
            py: 0.5,
          }}
        >
          <Box sx={{ flexGrow: 1, flexShrink: 0, display: "flex", alignItems: "center", gap: 1 }}>
            <NavigationBreadcrumbs
              items={breadcrumbItems}
              studyCount={studyIds.length}
              activeTree={activeTree}
              onNavigate={handleNavigate}
            />
          </Box>

          <BatchActions
            selectedStudyIds={selectedStudyIds}
            setSelectedStudyIds={setSelectedStudyIds}
          />

          <FilterControls
            showDescendants={showDescendants}
            isExternalRoot={isExternalRoot}
            isReferenceTypeActive={isReferenceStudyTypeActive}
            canScan={canScan}
            sortConfig={sortConfig}
            viewMode={viewMode}
            onToggleShowDescendants={handleToggleShowDescendants}
            onToggleStudyType={handleToggleStudyType}
            onScanDirectory={handleOpenScanDialog}
            onSortChange={handleSortChange}
            onViewModeChange={onViewModeChange}
          />
        </Box>
      </CustomScrollbar>

      <ScanDirectoryDialog
        open={confirmDirectoryScan}
        directoryPath={external.path}
        isRecursive={isRecursiveScan}
        showRecursiveOption={!isDesktopMode}
        onConfirm={handleConfirmScan}
        onCancel={handleCloseScanDialog}
        onToggleRecursive={handleToggleRecursiveScan}
      />
    </>
  );
}

export default Header;
