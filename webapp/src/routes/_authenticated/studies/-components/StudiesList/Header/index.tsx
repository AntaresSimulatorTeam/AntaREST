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

import { Box } from "@mui/material";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import CustomScrollbar from "@/components/CustomScrollbar";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import { updateStudyFilters, updateStudySortConfig } from "@/redux/ducks/studies";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getStudyFilters, getStudySortConfig, getStudiesById } from "@/redux/selectors";
import { directoryQueries } from "@/queries/directories/queries";
import { scanFolder } from "@/services/api/study";
import type { StudySortConfig } from "@/types/types";
import { toError } from "@/utils/fnUtils";
import { getDescendantIds } from "@/routes/_authenticated/studies/-components/StudyTree/ManagedTree/utils";
import BatchActions from "./BatchActions";
import DeleteStudiesDialog from "./DeleteStudiesDialog";
import MoveStudyDialog from "@/routes/-shared/components/studies/dialogs/MoveStudyDialog";
import FilterControls from "./FilterControls";
import { useBreadcrumbs } from "./hooks/useBreadcrumbs";
import NavigationBreadcrumbs from "./NavigationBreadcrumbs";
import ScanDirectoryDialog from "./ScanDirectoryDialog";
import type { BreadcrumbItem, HeaderProps } from "./types";

function Header({
  studyIds,
  selectedStudyIds,
  setSelectedStudyIds,
  setStudiesToLaunch,
  viewMode,
  onViewModeChange,
}: HeaderProps) {
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
  const [confirmDeleteStudies, setConfirmDeleteStudies] = useState(false);
  const [confirmMoveStudies, setConfirmMoveStudies] = useState(false);

  // Derived state
  const studiesById = useAppSelector(getStudiesById);
  const selectedStudies = selectedStudyIds.map((id) => studiesById[id]).filter(Boolean);
  const selectedManagedStudies = selectedStudies.filter((s) => s.managed);

  const isDesktopMode = import.meta.env.MODE === "desktop";
  const isReferenceStudyTypeActive = filters.type === "references";
  const canScan = activeTree === "external" && external.path !== "";
  const showDescendants =
    activeTree === "external" ? external.showDescendants : managed.showDescendants;

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

  const handleLaunchStudies = () => {
    setStudiesToLaunch(selectedStudyIds);
  };

  const handleDeleteStudies = () => {
    setConfirmDeleteStudies(true);
  };

  const handleCloseDeleteDialog = () => {
    setConfirmDeleteStudies(false);
    setSelectedStudyIds([]);
  };

  const handleMoveStudies = () => {
    setConfirmMoveStudies(true);
  };

  const handleCloseMoveDialog = () => {
    setConfirmMoveStudies(false);
    setSelectedStudyIds([]);
  };

  const handleDeselectAll = () => {
    setSelectedStudyIds([]);
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
              onNavigate={handleNavigate}
            />
          </Box>

          <BatchActions
            selectedCount={selectedStudyIds.length}
            managedCount={selectedManagedStudies.length}
            onLaunch={handleLaunchStudies}
            onMove={selectedManagedStudies.length > 0 ? handleMoveStudies : undefined}
            onDelete={selectedManagedStudies.length > 0 ? handleDeleteStudies : undefined}
            onDeselectAll={handleDeselectAll}
          />

          <FilterControls
            activeTree={activeTree}
            showDescendants={showDescendants}
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

      <DeleteStudiesDialog
        studyIds={selectedManagedStudies.map((s) => s.id)}
        open={confirmDeleteStudies}
        onClose={handleCloseDeleteDialog}
      />

      {confirmMoveStudies && (
        <MoveStudyDialog studies={selectedManagedStudies} open onClose={handleCloseMoveDialog} />
      )}
    </>
  );
}

export default Header;
