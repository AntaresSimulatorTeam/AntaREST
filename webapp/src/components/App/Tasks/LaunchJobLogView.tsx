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

import { useState } from "react";
import type { AxiosError } from "axios";
import { useTranslation } from "react-i18next";
import { Box, Tooltip } from "@mui/material";
import ErrorIcon from "@mui/icons-material/Error";
import InsertDriveFileIcon from "@mui/icons-material/InsertDriveFile";
import { getStudyJobLog } from "../../../services/api/study";
import LogModal from "../../common/LogModal";
import type { LaunchJob } from "../../../types/types";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";

interface PropsType {
  job: LaunchJob;
  logButton?: boolean;
  logErrorButton?: boolean;
}

function LaunchJobLogView(props: PropsType) {
  const { job, logButton, logErrorButton } = props;
  const [t] = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [jobIdDetail, setJobIdDetail] = useState<string>();
  const [followLogs, setFollowLogs] = useState<boolean>(false);
  const [logModalContent, setLogModalContent] = useState<string | undefined>();
  const [logModalContentLoading, setLogModalContentLoading] = useState<boolean>(false);

  const openLogView = (jobId: string, errorLogs = false) => {
    setJobIdDetail(jobId);
    setLogModalContentLoading(true);
    setFollowLogs(!errorLogs);
    (async () => {
      try {
        const logData = await getStudyJobLog(jobId, errorLogs ? "STDERR" : "STDOUT");
        setLogModalContent(logData);
      } catch (e) {
        enqueueErrorSnackbar(t("study.failtofetchlogs"), e as AxiosError);
      } finally {
        setLogModalContentLoading(false);
      }
    })();
  };

  return (
    <Box display="flex">
      {logButton && (
        <Tooltip title={t("global.logs") as string}>
          <Box
            sx={{
              width: "auto",
              height: "24px",
              cursor: "pointer",
              m: 0.5,
              "& svg:first-of-type": {
                color: "action.active",
              },
              "&:hover": {
                "& svg:first-of-type": {
                  color: "action.hover",
                },
              },
            }}
          >
            <InsertDriveFileIcon sx={{ fontSize: 22 }} onClick={() => openLogView(job.id)} />
          </Box>
        </Tooltip>
      )}
      {logErrorButton && (
        <Tooltip title={t("global.errorLogs") as string}>
          <Box
            sx={{
              position: "relative",
              width: "auto",
              height: "24px",
              cursor: "pointer",
              m: 0.5,
              "& svg:first-of-type": {
                color: "action.active",
              },
              "& svg:last-of-type": {
                position: "absolute",
                bottom: 0,
                right: 0,
                fontSize: 12,
                color: "error.light",
              },
              "&:hover": {
                "& svg:first-of-type": {
                  color: "action.hover",
                },
                "& svg:last-of-type": {
                  color: "error.dark",
                },
              },
            }}
            onClick={() => openLogView(job.id, true)}
          >
            <InsertDriveFileIcon sx={{ fontSize: 22 }} />
            <ErrorIcon />
          </Box>
        </Tooltip>
      )}
      <LogModal
        isOpen={!!jobIdDetail}
        followLogs={followLogs}
        jobId={jobIdDetail}
        content={logModalContent}
        loading={logModalContentLoading}
        close={() => setJobIdDetail(undefined)}
      />
    </Box>
  );
}

export default LaunchJobLogView;
