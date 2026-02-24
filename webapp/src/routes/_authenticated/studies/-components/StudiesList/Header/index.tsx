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
import { getStudyFilters, getStudySortConfig } from "@/redux/selectors";
import { directoryQueries } from "@/queries/directories/queries";
import { scanFolder } from "@/services/api/study";
import type { StudySortConfig } from "@/types/types";
import { toError } from "@/utils/fnUtils";
import { getDescendantIds } from "@/routes/_authenticated/studies/-components/StudyTree/ManagedTree/utils";
import BatchActions from "./BatchActions";
import DeleteStudiesDialog from "./DeleteStudiesDialog";
import FilterControls from "./FilterControls";
import { useBreadcrumbs } from "./hooks/useBreadcrumbs";
import NavigationBreadcrumbs from "./NavigationBreadcrumbs";
import ScanFolderDialog from "./ScanFolderDialog";
import type { BreadcrumbItem, HeaderProps } from "./types";

function Header({
  studyIds,
  selectedStudyIds,
  setSelectedStudyIds,
  setStudiesToLaunch,
}: HeaderProps) {
  const dispatch = useAppDispatch();
  const { t } = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  // Redux state
  const filters = useAppSelector(getStudyFilters);
  const { activeTree, managed, external } = filters;
  const sortConfig = useAppSelector(getStudySortConfig);

  // Local state
  const [confirmFolderScan, setConfirmFolderScan] = useState(false);
  const [isRecursiveScan, setIsRecursiveScan] = useState(false);
  const [confirmDeleteStudies, setConfirmDeleteStudies] = useState(false);

  // Derived state
  const isDesktopMode = import.meta.env.MODE === "desktop";
  const isReferenceStudyTypeActive = filters.type === "references";
  const canScan = activeTree === "external" && external.path !== "";

  // Breadcrumb navigation
  const breadcrumbItems = useBreadcrumbs({
    activeTree,
    managedDirectoryId: managed.directoryId,
    externalPath: external.path,
  });

  const { data: directories } = useSuspenseQuery(directoryQueries.list());

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
          external: { path: item.path ?? "", strictPath: external.strictPath },
        }),
      );
    }
  };

  const handleToggleStrictPath = () => {
    if (activeTree === "external") {
      dispatch(
        updateStudyFilters({
          external: { ...external, strictPath: !external.strictPath },
        }),
      );
    }
  };

  const handleToggleStudyType = () => {
    dispatch(updateStudyFilters({ type: filters.type !== "references" ? "references" : "all" }));
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

  const handleDeselectAll = () => {
    setSelectedStudyIds([]);
  };

  const handleOpenScanDialog = () => {
    setConfirmFolderScan(true);
  };

  const handleCloseScanDialog = () => {
    setConfirmFolderScan(false);
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
    setIsRecursiveScan(!isRecursiveScan);
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
              activeTree={activeTree}
            />
          </Box>

          <BatchActions
            selectedCount={selectedStudyIds.length}
            onLaunch={handleLaunchStudies}
            onDelete={handleDeleteStudies}
            onDeselectAll={handleDeselectAll}
          />

          <FilterControls
            activeTree={activeTree}
            strictPath={external.strictPath}
            isReferenceTypeActive={isReferenceStudyTypeActive}
            canScan={canScan}
            sortConfig={sortConfig}
            onToggleStrictPath={handleToggleStrictPath}
            onToggleStudyType={handleToggleStudyType}
            onScanFolder={handleOpenScanDialog}
            onSortChange={handleSortChange}
          />
        </Box>
      </CustomScrollbar>

      <ScanFolderDialog
        open={confirmFolderScan}
        folderPath={external.path}
        isRecursive={isRecursiveScan}
        showRecursiveOption={!isDesktopMode}
        onConfirm={handleConfirmScan}
        onCancel={handleCloseScanDialog}
        onToggleRecursive={handleToggleRecursiveScan}
      />

      <DeleteStudiesDialog
        studyIds={selectedStudyIds}
        open={confirmDeleteStudies}
        onClose={handleCloseDeleteDialog}
      />
    </>
  );
}

export default Header;
