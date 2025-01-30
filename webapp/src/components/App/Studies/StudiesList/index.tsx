/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
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

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Box,
  Typography,
  Breadcrumbs,
  Select,
  MenuItem,
  ListItemText,
  ListItemIcon,
  Tooltip,
  FormControl,
  InputLabel,
  IconButton,
  type SelectChangeEvent,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import NavigateNextIcon from "@mui/icons-material/NavigateNext";
import AutoSizer from "react-virtualized-auto-sizer";
import HomeIcon from "@mui/icons-material/Home";
import ArrowUpwardIcon from "@mui/icons-material/ArrowUpward";
import ArrowDownwardIcon from "@mui/icons-material/ArrowDownward";
import FolderIcon from "@mui/icons-material/Folder";
import AccountTreeIcon from "@mui/icons-material/AccountTree";
import RadarIcon from "@mui/icons-material/Radar";
import { FixedSizeGrid, type GridOnScrollProps } from "react-window";
import { v4 as uuidv4 } from "uuid";
import type { AxiosError } from "axios";
import type { StudyMetadata } from "../../../../common/types";
import { STUDIES_LIST_HEADER_HEIGHT } from "../../../../theme";
import {
  setStudyScrollPosition,
  updateStudiesSortConf,
  updateStudyFilters,
  type StudiesSortConf,
} from "../../../../redux/ducks/studies";
import LauncherDialog from "../LauncherDialog";
import useDebounce from "../../../../hooks/useDebounce";
import {
  getStudiesScrollPosition,
  getStudiesSortConf,
  getStudyFilters,
} from "../../../../redux/selectors";
import useAppSelector from "../../../../redux/hooks/useAppSelector";
import useAppDispatch from "../../../../redux/hooks/useAppDispatch";
import StudyCardCell from "./StudyCardCell";
import BatchModeMenu from "../BatchModeMenu";
import RefreshButton from "../RefreshButton";
import { scanFolder } from "../../../../services/api/study";
import useEnqueueErrorSnackbar from "../../../../hooks/useEnqueueErrorSnackbar";
import ConfirmationDialog from "../../../common/dialogs/ConfirmationDialog";
import CheckBoxFE from "@/components/common/fieldEditors/CheckBoxFE";
import { DEFAULT_WORKSPACE_PREFIX, ROOT_FOLDER_NAME } from "@/components/common/utils/constants";

const CARD_TARGET_WIDTH = 500;
const CARD_HEIGHT = 250;

export interface StudiesListProps {
  studyIds: Array<StudyMetadata["id"]>;
}

function StudiesList(props: StudiesListProps) {
  const { studyIds } = props;
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [t] = useTranslation();
  const [studyToLaunch, setStudyToLaunch] = useState<StudyMetadata["id"] | null>(null);
  const scrollPosition = useAppSelector(getStudiesScrollPosition);
  const sortConf = useAppSelector(getStudiesSortConf);
  const folder = useAppSelector((state) => getStudyFilters(state).folder);
  const strictFolderFilter = useAppSelector((state) => getStudyFilters(state).strictFolder);
  const [folderList, setFolderList] = useState(folder.split("/"));
  const dispatch = useAppDispatch();
  const sortLabelId = useRef(uuidv4()).current;
  const [selectedStudies, setSelectedStudies] = useState<string[]>([]);
  const [selectionMode, setSelectionMode] = useState(false);
  const [confirmFolderScan, setConfirmFolderScan] = useState(false);
  const [isRecursiveScan, setIsRecursiveScan] = useState(false);
  const isInDefaultWorkspace = !!folder && folder.startsWith(DEFAULT_WORKSPACE_PREFIX);
  const isRootFolder = folder === ROOT_FOLDER_NAME;
  const scanDisabled: boolean = isInDefaultWorkspace || isRootFolder;

  useEffect(() => {
    setFolderList(folder.split("/"));
  }, [folder]);

  useEffect(() => {
    if (!selectionMode) {
      setSelectedStudies([]);
    }
  }, [selectionMode]);

  useEffect(() => {
    if (selectedStudies.length === 0) {
      setSelectionMode(false);
    }
  }, [selectedStudies]);

  const sortOptions = useMemo<Array<StudiesSortConf & { name: string }>>(
    () => [
      {
        name: t("studies.sortByName"),
        property: "name",
        order: "ascend",
      },
      {
        name: t("studies.sortByName"),
        property: "name",
        order: "descend",
      },
      {
        name: t("studies.sortByDate"),
        property: "modificationDate",
        order: "ascend",
      },
      {
        name: t("studies.sortByDate"),
        property: "modificationDate",
        order: "descend",
      },
    ],
    [t],
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleScroll = useDebounce(
    (scrollProp: GridOnScrollProps) => {
      dispatch(setStudyScrollPosition(scrollProp.scrollTop));
    },
    { wait: 400, trailing: true },
  );

  const handleToggleSelectStudy = useCallback((sid: string) => {
    setSelectedStudies((prevState) => {
      const newSelectedStudies = prevState.filter((s) => s !== sid);
      if (newSelectedStudies.length !== prevState.length) {
        return newSelectedStudies;
      }
      return newSelectedStudies.concat([sid]);
    });
  }, []);

  const handleFolderScan = async (): Promise<void> => {
    try {
      // Remove "/root" from the path
      const folder = folderList.slice(1).join("/");
      await scanFolder(folder, isRecursiveScan);
      setConfirmFolderScan(false);
      setIsRecursiveScan(false);
    } catch (e) {
      enqueueErrorSnackbar(t("studies.error.scanFolder"), e as AxiosError);
    }
  };

  const handleRecursiveScan = () => {
    setIsRecursiveScan(!isRecursiveScan);
  };

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const setFolder = (value: string) => {
    dispatch(updateStudyFilters({ folder: value }));
  };

  const toggleStrictFolder = useCallback(() => {
    dispatch(updateStudyFilters({ strictFolder: !strictFolderFilter }));
  }, [dispatch, strictFolderFilter]);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      height={1}
      flex={1}
      display="flex"
      flexDirection="column"
      justifyContent="flex-start"
      alignItems="center"
      boxSizing="border-box"
      sx={{ overflowX: "hidden", overflowY: "hidden" }}
    >
      <Box
        width="100%"
        height={`${STUDIES_LIST_HEADER_HEIGHT}px`}
        px={2}
        display="flex"
        flexDirection="row"
        justifyContent="space-between"
        alignItems="center"
        boxSizing="border-box"
      >
        <Box
          display="flex"
          flexDirection="row"
          justifyContent="flex-start"
          alignItems="center"
          boxSizing="border-box"
        >
          <Breadcrumbs separator={<NavigateNextIcon fontSize="small" />} aria-label="breadcrumb">
            {folderList.map((fol, index) => {
              const path = folderList.slice(0, index + 1).join("/");
              if (index === 0) {
                return (
                  <HomeIcon
                    key={path}
                    sx={{
                      color: "text.primary",
                      cursor: "pointer",
                      "&:hover": {
                        color: "primary.main",
                      },
                    }}
                    onClick={() => setFolder("root")}
                  />
                );
              }
              return (
                <Typography
                  key={path}
                  sx={{
                    color: "text.primary",
                    cursor: "pointer",
                    "&:hover": {
                      textDecoration: "underline",
                      color: "primary.main",
                    },
                  }}
                  onClick={() => setFolder(path)}
                >
                  {fol}
                </Typography>
              );
            })}
          </Breadcrumbs>
          <Typography mx={2} sx={{ color: "white" }}>
            ({`${studyIds.length} ${t("global.studies").toLowerCase()}`})
          </Typography>

          {strictFolderFilter ? (
            <Tooltip title={t("studies.filters.strictfolder")}>
              <IconButton onClick={toggleStrictFolder}>
                <FolderIcon color="secondary" />
              </IconButton>
            </Tooltip>
          ) : (
            <Tooltip title={t("studies.filters.showChildrens")}>
              <IconButton onClick={toggleStrictFolder}>
                <AccountTreeIcon color="secondary" />
              </IconButton>
            </Tooltip>
          )}

          {!scanDisabled && (
            <Tooltip title={t("studies.scanFolder") as string}>
              <IconButton onClick={() => setConfirmFolderScan(true)} disabled={scanDisabled}>
                <RadarIcon />
              </IconButton>
            </Tooltip>
          )}
          {!isRootFolder && confirmFolderScan && (
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
              {`${t("studies.scanFolder")} ${folder}?`}
              <CheckBoxFE
                label={t("studies.recursiveScan")}
                value={isRecursiveScan}
                onChange={handleRecursiveScan}
              />
            </ConfirmationDialog>
          )}
        </Box>
        <Box
          display="flex"
          flexDirection="row"
          justifyContent="center"
          alignItems="center"
          boxSizing="border-box"
        >
          <BatchModeMenu
            selectedIds={selectedStudies}
            selectionMode={selectionMode}
            setSelectionMode={setSelectionMode}
          />
          <RefreshButton />
          <FormControl
            sx={{
              display: "flex",
              flexDirection: "column",
              justifyContent: "center",
              alignItems: "flex-start",
              boxSizing: "border-box",
            }}
          >
            <InputLabel id={sortLabelId} variant="standard">
              {t("studies.sortBy")}
            </InputLabel>
            <Select
              labelId={sortLabelId}
              value={JSON.stringify(sortConf)}
              label={t("studies.sortBy")}
              variant="filled"
              onChange={(e: SelectChangeEvent<string>) =>
                dispatch(updateStudiesSortConf(JSON.parse(e.target.value)))
              }
              sx={{
                width: "230px",
                height: "45px",
                ".MuiSelect-select": {
                  display: "flex",
                  flexFlow: "row nowrap",
                  justifyContent: "center",
                  alignItems: "center",
                },
                background: "rgba(255, 255, 255, 0)",
                borderRadius: "4px 4px 0px 0px",
                borderBottom: "1px solid rgba(255, 255, 255, 0.42)",
                ".MuiSelect-icon": {
                  backgroundColor: "#222333",
                },
              }}
            >
              {sortOptions.map(({ name, ...conf }) => {
                const value = JSON.stringify(conf);
                return (
                  <MenuItem
                    key={value}
                    value={value}
                    sx={{
                      display: "flex",
                      flexFlow: "row nowrap",
                      justifyContent: "center",
                      alignItems: "center",
                    }}
                  >
                    <ListItemIcon sx={{ minWidth: "30px" }}>
                      {conf.order === "ascend" ? <ArrowUpwardIcon /> : <ArrowDownwardIcon />}
                    </ListItemIcon>
                    <ListItemText primary={name} />
                  </MenuItem>
                );
              })}
            </Select>
          </FormControl>
        </Box>
      </Box>
      <Box sx={{ width: 1, height: 1 }}>
        <AutoSizer>
          {({ height, width }) => {
            const paddedWidth = width - 10;
            const columnWidth =
              paddedWidth / Math.max(Math.floor(paddedWidth / CARD_TARGET_WIDTH), 1);
            const columnCount = Math.floor(paddedWidth / columnWidth);
            const rowHeight = CARD_HEIGHT;

            return (
              <FixedSizeGrid
                key={studyIds.join()}
                columnCount={columnCount}
                columnWidth={columnWidth}
                height={height}
                width={width}
                rowCount={Math.ceil(studyIds.length / columnCount)}
                rowHeight={rowHeight}
                initialScrollTop={scrollPosition}
                onScroll={handleScroll}
                useIsScrolling
                itemData={{
                  studyIds,
                  setStudyToLaunch,
                  columnCount,
                  columnWidth,
                  rowHeight,
                  selectedStudies,
                  toggleSelect: handleToggleSelectStudy,
                  selectionMode,
                }}
              >
                {StudyCardCell}
              </FixedSizeGrid>
            );
          }}
        </AutoSizer>
      </Box>
      {studyToLaunch && (
        <LauncherDialog open studyIds={[studyToLaunch]} onClose={() => setStudyToLaunch(null)} />
      )}
    </Box>
  );
}

export default StudiesList;
