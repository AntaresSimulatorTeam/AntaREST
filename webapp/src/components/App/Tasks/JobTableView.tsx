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
  TableSortLabel,
  Tooltip,
  Typography,
  type SelectChangeEvent,
  type TableSortLabelProps,
} from "@mui/material";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useInterval } from "react-use";
import usePromiseWithSnackbarError from "../../../hooks/usePromiseWithSnackbarError";
import { getLauncherMetrics } from "../../../services/api/study";
import { TaskType } from "../../../services/api/tasks/constants";
import type { TaskView } from "../../../types/types";
import LinearProgressWithLabel from "../../common/LinearProgressWithLabel";
import UsePromiseCond from "../../common/utils/UsePromiseCond";
import * as R from "ramda";

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

interface Props {
  content: TaskView[];
  refresh: () => void;
}

function JobTableView(props: Props) {
  const { content, refresh } = props;
  const [t] = useTranslation();
  const [dateOrder, setDateOrder] = useState<NonNullable<TableSortLabelProps["direction"]>>("desc");
  const [filterType, setFilterType] = useState<FilterListType | "">("");
  const [filterRunningStatus, setFilterRunningStatus] = useState<boolean>(false);

  const launcherMetrics = usePromiseWithSnackbarError(getLauncherMetrics, {
    errorMessage: t("study.error.launchLoad"),
    deps: [],
  });

  // Refresh launcher metrics every minute
  useInterval(launcherMetrics.reload, 60_000);

  const displayContent = useMemo(() => {
    const filteredContent = R.filter(
      R.allPass(
        [
          filterRunningStatus && (({ status }: TaskView) => status === "running"),
          filterType && (({ type }: TaskView) => type === filterType),
        ].filter(Boolean),
      ),
      content,
    );

    return R.sort(
      dateOrder === "asc" ? R.ascend(R.prop("date")) : R.descend(R.prop("date")),
      filteredContent,
    );
  }, [content, dateOrder, filterRunningStatus, filterType]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleChange = (event: SelectChangeEvent<unknown>) => {
    setFilterType(event.target.value as FilterListType | "");
  };

  const handleFilterStatusChange = () => {
    setFilterRunningStatus(!filterRunningStatus);
  };

  const handleRequestDateSort = () => {
    setDateOrder(dateOrder === "asc" ? "desc" : "asc");
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

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
      <TableContainer component={Paper} elevation={2} sx={{ flex: 1 }}>
        <Table stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell>{t("global.jobs")}</TableCell>
              <TableCell align="right">{t("study.type")}</TableCell>
              <TableCell align="right">
                <TableSortLabel active direction={dateOrder} onClick={handleRequestDateSort}>
                  {t("global.date")}
                </TableSortLabel>
              </TableCell>
              <TableCell align="right">{t("tasks.action")}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {displayContent.map((row) => (
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
