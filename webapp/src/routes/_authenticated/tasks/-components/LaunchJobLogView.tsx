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

import LogModal from "@/components/LogModal";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import type { Job } from "@/services/api/launcher/jobs/types";
import { getStudyJobLog } from "@/services/api/study";
import ErrorIcon from "@mui/icons-material/Error";
import InsertDriveFileIcon from "@mui/icons-material/InsertDriveFile";
import { Badge, IconButton, Tooltip } from "@mui/material";
import type { AxiosError } from "axios";
import { useState } from "react";
import { useTranslation } from "react-i18next";

interface PropsType {
  job: Job;
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

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleOpenLogView = (jobId: string, errorLogs = false) => {
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

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      {logButton && (
        <Tooltip title={t("global.logs")}>
          <IconButton onClick={() => handleOpenLogView(job.id)} size="small">
            <InsertDriveFileIcon />
          </IconButton>
        </Tooltip>
      )}
      {logErrorButton && (
        <Tooltip title={t("global.errorLogs")}>
          <IconButton onClick={() => handleOpenLogView(job.id, true)} size="small">
            <Badge
              anchorOrigin={{
                vertical: "bottom",
                horizontal: "right",
              }}
              overlap="circular"
              badgeContent={<ErrorIcon sx={{ fontSize: 12, color: "error.light" }} />}
            >
              <InsertDriveFileIcon />
            </Badge>
          </IconButton>
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
    </>
  );
}

export default LaunchJobLogView;
