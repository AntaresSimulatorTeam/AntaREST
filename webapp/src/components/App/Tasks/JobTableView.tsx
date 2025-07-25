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
import CheckBoxFE from "@/components/common/fieldEditors/CheckBoxFE";
import SearchFE from "@/components/common/fieldEditors/SearchFE";
import SelectFE, { type SelectFEChangeEvent } from "@/components/common/fieldEditors/SelectFE";
import storage, { StorageKey } from "@/services/utils/localStorage";
import { isSearchMatching } from "@/utils/stringUtils";
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
  type TableSortLabelProps,
} from "@mui/material";
import * as R from "ramda";
import { useMemo, useState } from "react";
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

interface Props {
  content: TaskView[];
  refresh: () => void;
}

function JobTableView(props: Props) {
  const { content, refresh } = props;
  const [t] = useTranslation();
  const [orderBy, setOrderBy] = useState<"date" | "user">("date");
  const [orderDirection, setOrderDirection] =
    useState<NonNullable<TableSortLabelProps["direction"]>>("desc");
  const [filterType, setFilterType] = useState<FilterListType | "">("");
  const [filterUser, setFilterUser] = useState(storage.getItem(StorageKey.TasksFilterUser) || "");
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
          filterUser && (({ userName }: TaskView) => isSearchMatching(filterUser, userName || "")),
        ].filter(Boolean),
      ),
      content,
    );

    const getUserName = R.compose(R.toLower, R.propOr("", "userName"));

    const criterion: (t: TaskView) => string = orderBy === "date" ? R.prop("date") : getUserName;
    return R.sort(
      orderDirection === "asc" ? R.ascend(criterion) : R.descend(criterion),
      filteredContent,
    );
  }, [content, orderBy, orderDirection, filterRunningStatus, filterType, filterUser]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleChange = (event: SelectFEChangeEvent<FilterListType, true>) => {
    setFilterType(event.target.value);
  };

  const handleFilterStatusChange = () => {
    setFilterRunningStatus(!filterRunningStatus);
  };

  const handleRequestSort = (column: "date" | "user") => {
    const isAsc = orderBy === column && orderDirection === "asc";
    setOrderDirection(isAsc ? "desc" : "asc");
    setOrderBy(column);
  };

  const handleUserValueFilterChange = (input: string) => {
    setFilterUser(input);
    storage.setItem(StorageKey.TasksFilterUser, input);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////
  return (
    <>
      {/* Header */}
      <CustomScrollbar>
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: 1,
            px: 1,
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

            <SearchFE
              size="extra-small"
              value={filterUser}
              onSearchValueChange={handleUserValueFilterChange}
              sx={{ maxWidth: 200 }}
              label={t("global.user")}
            />
            <SelectFE
              label={t("tasks.typeFilter")}
              value={filterType}
              onChange={(e) => handleChange(e)}
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
      </CustomScrollbar>
      {/* List */}
      <TableContainer component={Paper} elevation={2} sx={{ flex: 1 }}>
        <Table stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell>{t("global.jobs")}</TableCell>
              <TableCell align="right">{t("study.type")}</TableCell>
              <TableCell align="right">
                <TableSortLabel
                  active={orderBy === "date"}
                  direction={orderBy === "date" ? orderDirection : "asc"}
                  onClick={() => handleRequestSort("date")}
                >
                  {t("global.date")}
                </TableSortLabel>
              </TableCell>
              <TableCell align="right">
                <TableSortLabel
                  active={orderBy === "user"}
                  direction={orderBy === "user" ? orderDirection : "asc"}
                  onClick={() => handleRequestSort("user")}
                >
                  {t("global.user")}
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
                <TableCell align="right">{row.userName || ""}</TableCell>
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
