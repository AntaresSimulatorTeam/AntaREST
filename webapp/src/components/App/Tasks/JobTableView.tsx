/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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
import { useTranslation } from "react-i18next";
import { useInterval } from "react-use";

import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown";
import ArrowDropUpIcon from "@mui/icons-material/ArrowDropUp";
import RefreshIcon from "@mui/icons-material/Refresh";
import {
  Box,
  Button,
  Checkbox,
  FormControl,
  FormControlLabel,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  SelectChangeEvent,
  Skeleton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
} from "@mui/material";
import { grey } from "@mui/material/colors";

import { TaskType, TaskView } from "@/common/types";
import LinearProgressWithLabel from "@/components/common/LinearProgressWithLabel";
import UsePromiseCond from "@/components/common/utils/UsePromiseCond";
import usePromiseWithSnackbarError from "@/hooks/usePromiseWithSnackbarError";
import { getLauncherMetrics } from "@/services/api/study";

interface PropType {
  content: TaskView[];
  refresh: () => void;
}

function JobTableView(props: PropType) {
  const { content, refresh } = props;
  const [t] = useTranslation();
  const [sorted, setSorted] = useState<string>();
  const [type, setType] = useState<string>("all");
  const [filterRunningStatus, setFilterRunningStatus] =
    useState<boolean>(false);
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
      if (type !== "all") {
        filteredContent = filteredContent.filter((o) => o.type === type);
      }
      return filteredContent;
    },
    [type, filterRunningStatus],
  );

  const handleChange = (event: SelectChangeEvent) => {
    setType(event.target.value as string);
  };

  const handleFilterStatusChange = () => {
    setFilterRunningStatus(!filterRunningStatus);
  };

  const filterList = [
    "all",
    TaskType.DOWNLOAD,
    TaskType.LAUNCH,
    TaskType.COPY,
    TaskType.ARCHIVE,
    TaskType.UNARCHIVE,
    TaskType.UPGRADE_STUDY,
    TaskType.SCAN,
  ];

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
            ifResolved={(data) => (
              <>
                <Typography>{t("study.allocatedCpuRate")}</Typography>
                <LinearProgressWithLabel
                  indicator={Math.floor(data.allocatedCpuRate)}
                  size="20%"
                  tooltip={t("study.allocatedCpuRate")}
                  gradiant
                />
                <Typography>{t("study.clusterLoadRate")}</Typography>
                <LinearProgressWithLabel
                  indicator={Math.floor(data.clusterLoadRate)}
                  size="20%"
                  tooltip={t("study.clusterLoadRate")}
                  gradiant
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
            control={
              <Checkbox
                checked={filterRunningStatus}
                onChange={handleFilterStatusChange}
              />
            }
            label={t("tasks.runningTasks") as string}
          />
          <FormControl variant="outlined" sx={{ m: 1, mr: 3, minWidth: 160 }}>
            <InputLabel id="jobsView-select-outlined-label">
              {t("tasks.typeFilter")}
            </InputLabel>
            <Select
              labelId="jobsView-select-outlined-label"
              id="jobsView-select-outlined"
              value={type}
              onChange={handleChange}
              label={t("tasks.typeFilter")}
            >
              {filterList.map((item) => (
                <MenuItem value={item} key={item}>
                  {t(`tasks.${item}`)}
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
                  color: grey[500],
                },
              }}
            >
              <TableCell>{t("global.jobs")}</TableCell>
              <TableCell align="right">{t("study.type")}</TableCell>
              <TableCell align="right">
                <Box
                  display="flex"
                  alignItems="center"
                  justifyContent="flex-end"
                >
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
                  <TableCell align="right">{t(`tasks.${row.type}`)}</TableCell>
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
