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

import { useCallback, useEffect, useState } from "react";
import moment from "moment";
import {
  Paper,
  TableContainer,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tooltip,
  Button,
  Checkbox,
  FormControlLabel,
  Typography,
  Skeleton,
  colors,
  type SelectChangeEvent,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import RefreshIcon from "@mui/icons-material/Refresh";
import ArrowDropUpIcon from "@mui/icons-material/ArrowDropUp";
import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown";
import type { TaskView } from "../../../types/types";
import usePromiseWithSnackbarError from "../../../hooks/usePromiseWithSnackbarError";
import { getLauncherMetrics } from "../../../services/api/study";
import LinearProgressWithLabel from "../../common/LinearProgressWithLabel";
import UsePromiseCond from "../../common/utils/UsePromiseCond";
import { useInterval } from "react-use";
import { TaskType } from "../../../services/api/tasks/constants";

const FILTER_LIST: Array<TaskView["type"]> = [
  "DOWNLOAD",
  "LAUNCH",
  TaskType.Copy,
  TaskType.Archive,
  TaskType.Unarchive,
  TaskType.UpgradeStudy,
  TaskType.ThermalClusterSeriesGeneration,
  TaskType.Scan,
  "UNKNOWN",
];

type FilterListType = (typeof FILTER_LIST)[number];

interface PropType {
  content: TaskView[];
  refresh: () => void;
}

function JobTableView(props: PropType) {
  const { content, refresh } = props;
  const [t] = useTranslation();
  const [sorted, setSorted] = useState<string>();
  const [filterType, setFilterType] = useState<FilterListType | "">("");
  const [filterRunningStatus, setFilterRunningStatus] = useState<boolean>(false);
  const [currentContent, setCurrentContent] = useState<TaskView[]>(content);

  const launcherMetrics = usePromiseWithSnackbarError(getLauncherMetrics, {
    errorMessage: t("study.error.launchLoad"),
    deps: [],
  });

  const applyFilter = useCallback(
    (taskList: TaskView[]) => {
      let filteredContent = taskList;
      if (filterRunningStatus) {
        filteredContent = filteredContent.filter((o) => o.status === "running");
      }
      if (filterType) {
        filteredContent = filteredContent.filter((o) => o.type === filterType);
      }
      return filteredContent;
    },
    [filterType, filterRunningStatus],
  );

  const handleChange = (event: SelectChangeEvent) => {
    setFilterType(event.target.value as FilterListType | "");
  };

  const handleFilterStatusChange = () => {
    setFilterRunningStatus(!filterRunningStatus);
  };

  useEffect(() => {
    setCurrentContent(applyFilter(content));
  }, [content, applyFilter]);

  // Refresh launcher metrics every minute
  useInterval(launcherMetrics.reload, 60_000);

  return (
    <Box
      sx={{
        flexGrow: 1,
        mx: 1,
        my: 2,
        overflowX: "hidden",
        overflowY: "auto",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          ml: 2,
        }}
      >
        <Box
          sx={{
            width: "60%",
            display: "flex",
            alignContent: "center",
            alignSelf: "center",
            gap: 1,
          }}
        >
          <UsePromiseCond
            response={launcherMetrics}
            keepLastResolvedOnReload
            ifFulfilled={(data) => (
              <>
                <Typography>{t("study.allocatedCpuRate")}</Typography>
                <LinearProgressWithLabel
                  value={Math.floor(data.allocatedCpuRate)}
                  tooltip={t("study.allocatedCpuRate")}
                  sx={{ width: "20%" }}
                />
                <Typography>{t("study.clusterLoadRate")}</Typography>
                <LinearProgressWithLabel
                  value={Math.floor(data.clusterLoadRate)}
                  tooltip={t("study.clusterLoadRate")}
                  sx={{ width: "20%" }}
                />
                <Typography>
                  {t("study.nbQueuedJobs")}: {data.nbQueuedJobs}
                </Typography>
              </>
            )}
            ifPending={() => <Skeleton width={300} />}
          />
        </Box>
        <Box display="flex" alignItems="center">
          <Tooltip title={t("tasks.refresh") as string} sx={{ mr: 4 }}>
            <Button
              color="primary"
              onClick={() => {
                refresh();
                launcherMetrics.reload();
              }}
              variant="outlined"
            >
              <RefreshIcon />
            </Button>
          </Tooltip>
          <FormControlLabel
            control={<Checkbox checked={filterRunningStatus} onChange={handleFilterStatusChange} />}
            label={t("tasks.runningTasks") as string}
          />
          <FormControl variant="outlined" sx={{ m: 1, mr: 3, minWidth: 160 }}>
            <InputLabel id="jobsView-select-outlined-label">{t("tasks.typeFilter")}</InputLabel>
            <Select
              labelId="jobsView-select-outlined-label"
              id="jobsView-select-outlined"
              value={filterType}
              onChange={handleChange}
              label={t("tasks.typeFilter")}
            >
              <MenuItem value="">
                <em>{t("global.none")}</em>
              </MenuItem>
              {FILTER_LIST.map((item) => (
                <MenuItem value={item} key={item}>
                  {t(`tasks.type.${item}`)}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>
      </Box>
      <TableContainer component={Paper}>
        <Table sx={{ width: "100%", height: "90%" }} aria-label="simple table">
          <TableHead>
            <TableRow
              sx={{
                "& td, & th": {
                  borderBottom: "1px solid",
                  borderColor: "divider",
                  color: colors.grey[500],
                },
              }}
            >
              <TableCell>{t("global.jobs")}</TableCell>
              <TableCell align="right">{t("study.type")}</TableCell>
              <TableCell align="right">
                <Box display="flex" alignItems="center" justifyContent="flex-end">
                  {t("global.date")}
                  {!sorted ? (
                    <ArrowDropUpIcon
                      sx={{
                        cursor: "pointer",
                        color: "action.active",
                        "&:hover": { color: "action.hover" },
                      }}
                      onClick={() => setSorted("date")}
                    />
                  ) : (
                    <ArrowDropDownIcon
                      sx={{
                        cursor: "pointer",
                        color: "action.active",
                        "&:hover": { color: "action.hover" },
                      }}
                      onClick={() => setSorted(undefined)}
                    />
                  )}
                </Box>
              </TableCell>
              <TableCell align="right">{t("tasks.action")}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {currentContent
              .sort((a, b) => {
                if (!sorted && sorted !== "date") {
                  return moment(a.date).isAfter(moment(b.date)) ? -1 : 1;
                }
                return moment(a.date).isAfter(moment(b.date)) ? 1 : -1;
              })
              .map((row) => (
                <TableRow
                  key={`job-${row.id}`}
                  sx={{
                    "& td, & th": {
                      borderColor: "divider",
                    },
                    "&:last-child > td, &:last-child > th": {
                      border: 0,
                    },
                  }}
                >
                  <TableCell component="th" scope="row">
                    {row.name}
                  </TableCell>
                  <TableCell align="right">{t(`tasks.type.${row.type}`)}</TableCell>
                  <TableCell align="right">{row.dateView}</TableCell>
                  <TableCell align="right">{row.action}</TableCell>
                </TableRow>
              ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}

export default JobTableView;
