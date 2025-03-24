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

import CheckBoxFE from "@/components/common/fieldEditors/CheckBoxFE";
import SelectFE from "@/components/common/fieldEditors/SelectFE";
import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown";
import ArrowDropUpIcon from "@mui/icons-material/ArrowDropUp";
import RefreshIcon from "@mui/icons-material/Refresh";
import {
  Box,
  IconButton,
  Paper,
  Skeleton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
  type SelectChangeEvent,
} from "@mui/material";
import moment from "moment";
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useInterval } from "react-use";
import usePromiseWithSnackbarError from "../../../hooks/usePromiseWithSnackbarError";
import { getLauncherMetrics } from "../../../services/api/study";
import { TaskType } from "../../../services/api/tasks/constants";
import type { TaskView } from "../../../types/types";
import LinearProgressWithLabel from "../../common/LinearProgressWithLabel";
import UsePromiseCond from "../../common/utils/UsePromiseCond";

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

  const handleChange = (event: SelectChangeEvent<unknown>) => {
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
    <>
      {/* Header */}
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: 1,
          px: 1,
          overflowX: "auto",
          overflowY: "hidden",
        }}
      >
        <Box
          sx={{
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
                <Typography fontSize="small" sx={{ textWrap: "nowrap" }}>
                  {t("study.allocatedCpuRate")}
                </Typography>
                <LinearProgressWithLabel
                  value={Math.floor(data.allocatedCpuRate)}
                  tooltip={t("study.allocatedCpuRate")}
                  sx={{ width: 100 }}
                />
                <Typography fontSize="small" sx={{ textWrap: "nowrap" }}>
                  {t("study.clusterLoadRate")}
                </Typography>
                <LinearProgressWithLabel
                  value={Math.floor(data.clusterLoadRate)}
                  tooltip={t("study.clusterLoadRate")}
                  sx={{ width: 100 }}
                />
                <Typography fontSize="small" sx={{ textWrap: "nowrap" }}>
                  {t("study.nbQueuedJobs")}: {data.nbQueuedJobs}
                </Typography>
              </>
            )}
            ifPending={() => <Skeleton width={300} />}
          />
        </Box>
        <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
          <Tooltip title={t("tasks.refresh")}>
            <IconButton
              onClick={() => {
                refresh();
                launcherMetrics.reload();
              }}
            >
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <CheckBoxFE
            label={t("tasks.runningTasks")}
            value={filterRunningStatus}
            onChange={handleFilterStatusChange}
            sx={{ textWrap: "nowrap" }}
          />
          <SelectFE
            label={t("tasks.typeFilter")}
            value={filterType}
            onChange={handleChange}
            emptyValue
            options={FILTER_LIST.map((item) => ({
              value: item,
              label: t(`tasks.type.${item}`),
            }))}
            size="extra-small"
            margin="dense"
            sx={{ minWidth: 160 }}
          />
        </Box>
      </Box>
      {/* List */}
      <TableContainer component={Paper} elevation={2}>
        <Table stickyHeader>
          <TableHead>
            <TableRow>
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
                <TableRow key={row.id}>
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
    </>
  );
}

export default JobTableView;
