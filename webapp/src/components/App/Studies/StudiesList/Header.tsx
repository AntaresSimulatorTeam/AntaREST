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

import CustomScrollbar from "@/components/common/CustomScrollbar";
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
import HomeIcon from "@mui/icons-material/Home";
import FolderIcon from "@mui/icons-material/Folder";
import AccountTreeIcon from "@mui/icons-material/AccountTree";
import RadarIcon from "@mui/icons-material/Radar";
import RefreshButton from "@/components/App/Studies/RefreshButton";
import SelectFE from "@/components/common/fieldEditors/SelectFE";
import { updateStudiesSortConf, updateStudyFilters } from "@/redux/ducks/studies";
import { useCallback, useEffect, useState } from "react";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getStudiesSortConf, getStudyFilters } from "@/redux/selectors";
import type { StudyMetadata } from "@/types/types";
import ConfirmationDialog from "@/components/common/dialogs/ConfirmationDialog";
import CheckBoxFE from "@/components/common/fieldEditors/CheckBoxFE";
import { scanFolder } from "@/services/api/study";
import type { AxiosError } from "axios";
import { useTranslation } from "react-i18next";
import ArrowUpwardIcon from "@mui/icons-material/ArrowUpward";
import ArrowDownwardIcon from "@mui/icons-material/ArrowDownward";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import BoltIcon from "@mui/icons-material/Bolt";
import CheckBoxIcon from "@mui/icons-material/CheckBox";

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

export interface Props {
  studyIds: Array<StudyMetadata["id"]>;
  selectedStudyIds: Array<StudyMetadata["id"]>;
  setSelectedStudyIds: (ids: Array<StudyMetadata["id"]>) => void;
  setStudiesToLaunch: (ids: Array<StudyMetadata["id"]>) => void;
}

function Header({ studyIds, selectedStudyIds, setSelectedStudyIds, setStudiesToLaunch }: Props) {
  const folder = useAppSelector((state) => getStudyFilters(state).folder);
  const strictFolderFilter = useAppSelector((state) => getStudyFilters(state).strictFolder);
  const sortConf = useAppSelector(getStudiesSortConf);
  const [folderList, setFolderList] = useState(folder.split("/"));
  const [confirmFolderScan, setConfirmFolderScan] = useState(false);
  const [isRecursiveScan, setIsRecursiveScan] = useState(false);
  const dispatch = useAppDispatch();
  const { t } = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const hasStudiesSelected = selectedStudyIds.length > 0;

  useEffect(() => {
    setFolderList(folder.split("/"));
  }, [folder]);

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
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleFolderScan = async () => {
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
      <CustomScrollbar options={{ overflow: { y: "hidden" } }}>
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
              {folderList.map((folder, index) => {
                const path = folderList.slice(0, index + 1).join("/");
                const isRoot = index === 0;

                return (
                  <Link
                    key={path}
                    underline={isRoot ? "none" : "hover"}
                    color="inherit"
                    onClick={() => setFolder(isRoot ? "root" : path)}
                    sx={{ display: "flex", alignItems: "center" }}
                    href="#"
                  >
                    {isRoot ? <HomeIcon fontSize="inherit" /> : folder}
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
          <ToggleButtonGroup
            value={strictFolderFilter}
            exclusive
            onChange={toggleStrictFolder}
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
          {folder !== "root" && (
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
          {`${t("studies.scanFolder")} ${folder}?`}
          <CheckBoxFE
            label={t("studies.recursiveScan")}
            value={isRecursiveScan}
            onChange={handleRecursiveScan}
          />
        </ConfirmationDialog>
      )}
    </>
  );
}

export default Header;
