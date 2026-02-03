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
import ConfirmationDialog from "@/components/dialogs/ConfirmationDialog";
import CheckBoxFE from "@/components/fieldEditors/CheckBoxFE";
import SelectFE from "@/components/fieldEditors/SelectFE";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import { updateStudiesSortConf, updateStudyFilters } from "@/redux/ducks/studies";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getStudiesSortConf, getStudyFilters } from "@/redux/selectors";
import RefreshButton from "@/routes/_authenticated/studies/-components/RefreshButton";
import { scanFolder } from "@/services/api/study";
import type { StudyMetadata } from "@/types/types";
import AccountTreeIcon from "@mui/icons-material/AccountTree";
import ArrowDownwardIcon from "@mui/icons-material/ArrowDownward";
import ArrowUpwardIcon from "@mui/icons-material/ArrowUpward";
import BoltIcon from "@mui/icons-material/Bolt";
import CheckBoxIcon from "@mui/icons-material/CheckBox";
import FolderIcon from "@mui/icons-material/Folder";
import LayersIcon from "@mui/icons-material/Layers";
import LayersClearIcon from "@mui/icons-material/LayersClear";
import RadarIcon from "@mui/icons-material/Radar";
import {
  Box,
  Breadcrumbs,
  Button,
  IconButton,
  Link,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip,
  Typography,
} from "@mui/material";
import { getRouteApi } from "@tanstack/react-router";
import type { AxiosError } from "axios";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { buildDirectoryTree, getDirectoryPath } from "../StudyTree/ManagedTree/utils";

const routeApi = getRouteApi("/_authenticated/studies/");

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

interface BreadcrumbItem {
  label: string;
  id: string | null;
  path: string | null;
}

export interface Props {
  studyIds: Array<StudyMetadata["id"]>;
  selectedStudyIds: Array<StudyMetadata["id"]>;
  setSelectedStudyIds: (ids: Array<StudyMetadata["id"]>) => void;
  setStudiesToLaunch: (ids: Array<StudyMetadata["id"]>) => void;
}

function Header({ studyIds, selectedStudyIds, setSelectedStudyIds, setStudiesToLaunch }: Props) {
  const filters = useAppSelector(getStudyFilters);
  const { activeTree, managed, external } = filters;
  const studyTypeFilter = filters.type;
  const sortConf = useAppSelector(getStudiesSortConf);
  const [confirmFolderScan, setConfirmFolderScan] = useState(false);
  const [isRecursiveScan, setIsRecursiveScan] = useState(false);
  const dispatch = useAppDispatch();
  const { t } = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const hasStudiesSelected = selectedStudyIds.length > 0;
  const isDesktopMode = import.meta.env.MODE === "desktop";
  const isReferenceStudyTypeActive = studyTypeFilter === "references";

  const directories = routeApi.useLoaderData();

  const breadcrumbItems = useMemo((): BreadcrumbItem[] => {
    const homeItem: BreadcrumbItem = {
      label: t("studies.tree.home", { defaultValue: "root" }),
      id: null,
      path: null,
    };

    if (activeTree === "managed") {
      // For managed tree, use directory utilities to build path
      if (!managed.directoryId) {
        return [homeItem];
      }

      const directoryTree = buildDirectoryTree(directories);
      const pathIds = getDirectoryPath(directoryTree, managed.directoryId);
      const directoriesById = Object.fromEntries(directories.map((d) => [d.id, d]));

      return [
        homeItem,
        ...pathIds.map(
          (id): BreadcrumbItem => ({
            label: directoriesById[id].name,
            id,
            path: null,
          }),
        ),
      ];
    }

    // For external tree, build path from filesystem path string
    if (!external.path) {
      return [homeItem];
    }

    const pathParts = external.path.split("/").filter(Boolean);
    return [
      homeItem,
      ...pathParts.map(
        (part, index): BreadcrumbItem => ({
          label: part,
          id: null,
          path: `/${pathParts.slice(0, index + 1).join("/")}`,
        }),
      ),
    ];
  }, [activeTree, managed.directoryId, external.path, directories, t]);

  const canScan = activeTree === "external" && external.path !== "";

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const navigateTo = (item: BreadcrumbItem) => {
    if (activeTree === "managed") {
      dispatch(
        updateStudyFilters({
          activeTree: "managed",
          managed: { directoryId: item.id },
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

  const toggleStrictFolderFilter = () => {
    if (activeTree === "external") {
      dispatch(
        updateStudyFilters({
          external: { ...external, strictPath: !external.strictPath },
        }),
      );
    }
  };

  const toggleStudyTypeFilter = () => {
    dispatch(updateStudyFilters({ type: studyTypeFilter !== "references" ? "references" : "all" }));
  };

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleFolderScan = async () => {
    try {
      // Only scan for external tree
      if (activeTree === "external" && external.path) {
        await scanFolder(external.path, isRecursiveScan);
      }
      setConfirmFolderScan(false);
      setIsRecursiveScan(false);
    } catch (e) {
      enqueueErrorSnackbar(t("studies.error.scanFolder"), e as AxiosError);
    }
  };

  const handleRecursiveScan = () => {
    setIsRecursiveScan(!isRecursiveScan);
  };

  const handleLaunchStudy = () => {
    setStudiesToLaunch(selectedStudyIds);
  };

  const handleDeselectAll = () => {
    setSelectedStudyIds([]);
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
          <Box sx={{ flexGrow: 1, flexShrink: 0, display: "flex", alignItems: "center", gap: 1.5 }}>
            <Breadcrumbs maxItems={3}>
              {breadcrumbItems.map((item, index) => {
                const isLast = index === breadcrumbItems.length - 1;

                return (
                  <Link
                    key={activeTree === "managed" ? (item.id ?? "root") : (item.path ?? "root")}
                    underline="hover"
                    color="inherit"
                    onClick={() => !isLast && navigateTo(item)}
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      cursor: isLast ? "default" : "pointer",
                      fontWeight: isLast ? 600 : 400,
                    }}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </Breadcrumbs>
            <Typography fontSize="small">
              ({`${studyIds.length} ${t("global.studies").toLowerCase()}`})
            </Typography>
          </Box>
          {hasStudiesSelected && (
            <>
              <Tooltip title={t("studies.batchMode")}>
                <Button onClick={handleLaunchStudy} color="primary">
                  <BoltIcon />
                  {t("global.launch")} ({selectedStudyIds.length})
                </Button>
              </Tooltip>
              <Tooltip title={t("studies.deselectAll")}>
                <IconButton color="primary" onClick={handleDeselectAll}>
                  <CheckBoxIcon />
                </IconButton>
              </Tooltip>
            </>
          )}
          {activeTree === "external" && (
            <ToggleButtonGroup
              value={external.strictPath}
              exclusive
              onChange={toggleStrictFolderFilter}
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
          )}
          <Tooltip
            title={
              isReferenceStudyTypeActive
                ? t("studies.filters.disableReferenceType")
                : t("studies.filters.enableReferenceType")
            }
          >
            <IconButton onClick={toggleStudyTypeFilter}>
              {isReferenceStudyTypeActive ? <LayersClearIcon /> : <LayersIcon />}
            </IconButton>
          </Tooltip>
          {canScan && (
            <Tooltip title={t("studies.scanFolder")}>
              <IconButton onClick={() => setConfirmFolderScan(true)}>
                <RadarIcon />
              </IconButton>
            </Tooltip>
          )}
          <RefreshButton mini />
          <SelectFE
            size="extra-small"
            label={t("studies.sortBy")}
            value={JSON.stringify(sortConf)}
            onChange={(event) =>
              dispatch(updateStudiesSortConf(JSON.parse(event.target.value as string)))
            }
            options={sortOptions.map(({ labelKey, ...rest }) => ({
              label: t(labelKey),
              ...rest,
            }))}
            sx={{ minWidth: 90 }}
            margin="dense"
          />
        </Box>
      </CustomScrollbar>
      {confirmFolderScan && (
        <ConfirmationDialog
          titleIcon={RadarIcon}
          onCancel={() => {
            setConfirmFolderScan(false);
            setIsRecursiveScan(false);
          }}
          onConfirm={handleFolderScan}
          alert="warning"
          open
        >
          {`${t("studies.scanFolder")} ${activeTree === "external" ? external.path : ""}?`}
          {!isDesktopMode && (
            <CheckBoxFE
              label={t("studies.recursiveScan")}
              value={isRecursiveScan}
              onChange={handleRecursiveScan}
            />
          )}
        </ConfirmationDialog>
      )}
    </>
  );
}

export default Header;
