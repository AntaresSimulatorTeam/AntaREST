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

import FiberManualRecordIcon from "@mui/icons-material/FiberManualRecord";
import BlockIcon from "@mui/icons-material/Block";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import EqualizerIcon from "@mui/icons-material/Equalizer";
import { Tooltip, Typography, Stepper, Step, StepLabel } from "@mui/material";
import moment from "moment";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import type { AxiosError } from "axios";
import type { JobStatus, LaunchJob, LaunchJobsProgress } from "@/types/types";
import { convertUTCToLocalTime } from "@/services/utils";
import { getStudyOutputs, killStudy } from "@/services/api/study";
import LaunchJobLogView from "../../../../Tasks/LaunchJobLogView";
import useEnqueueErrorSnackbar from "../../../../../../hooks/useEnqueueErrorSnackbar";
import {
  CancelContainer,
  JobRoot,
  QontoConnector,
  QontoStepIconRoot,
  StepLabelRoot,
  StepLabelRow,
} from "./style";
import ConfirmationDialog from "../../../../../common/dialogs/ConfirmationDialog";
import LinearProgressWithLabel from "../../../../../common/LinearProgressWithLabel";
import type { EmptyObject } from "@/utils/tsUtils";
import DigestDialog from "@/components/common/dialogs/DigestDialog";
import usePromiseWithSnackbarError from "@/hooks/usePromiseWithSnackbarError";

export const ColorStatus = {
  running: "warning.main",
  pending: "grey.400",
  success: "success.main",
  failed: "error.main",
} as const;

const iconStyle = {
  m: 0.5,
  height: 22,
  cursor: "pointer",
  "&:hover": {
    color: "action.hover",
  },
};

function QontoStepIcon(props: { className: string | undefined; status: JobStatus }) {
  const { className, status } = props;
  return (
    <QontoStepIconRoot className={className}>
      <FiberManualRecordIcon
        sx={{
          width: 24,
          height: 24,
          color: ColorStatus[status],
        }}
      />
    </QontoStepIconRoot>
  );
}

type DialogState =
  | {
      type: "killJob" | "digest";
      job: LaunchJob;
    }
  | EmptyObject;

interface Props {
  studyId: string;
  jobs: LaunchJob[];
  jobsProgress: LaunchJobsProgress;
}

function JobStepper({ studyId, jobs, jobsProgress }: Props) {
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [dialogState, setDialogState] = useState<DialogState>({});

  const { data: outputs, isLoading: outputsLoading } = usePromiseWithSnackbarError(
    () => getStudyOutputs(studyId),
    {
      errorMessage: t("results.error.outputs"),
      deps: [studyId],
    },
  );

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const canDisplayDigest = (job: LaunchJob) => {
    if (job.status !== "success") {
      return false;
    }

    const output = outputs?.find((output) => output.name === job.outputId);
    return !!output?.settings?.output?.synthesis;
  };

  const closeDialog = () => setDialogState({});

  ////////////////////////////////////////////////////////////////
  // Actions
  ////////////////////////////////////////////////////////////////

  const killTask = async (jobId: LaunchJob["id"]) => {
    closeDialog();

    try {
      await killStudy(jobId);
    } catch (e) {
      enqueueErrorSnackbar(t("study.failtokilltask"), e as AxiosError);
    }
  };

  const copyId = (jobId: LaunchJob["id"]) => {
    try {
      navigator.clipboard.writeText(jobId);

      enqueueSnackbar(t("study.success.jobIdCopy"), {
        variant: "success",
      });
    } catch (e) {
      enqueueErrorSnackbar(t("study.error.jobIdCopy"), e as AxiosError);
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <JobRoot jobLength={jobs.length}>
      <Stepper
        activeStep={-1}
        orientation="vertical"
        connector={<QontoConnector />}
        sx={{ width: "100%", px: 2, boxSizing: "border-box" }}
      >
        {jobs.map((job) => (
          <Step key={job.id}>
            <StepLabel
              icon={<QontoStepIcon className={undefined} status={job.status} />}
              sx={{
                display: "flex",
                justifyContent: "flex-start",
                alignItems: "flex-start",
                mt: 1,
              }}
            >
              <StepLabelRoot>
                <StepLabelRow>
                  <Typography
                    sx={{
                      height: "auto",
                      mx: 0,
                      boxSizing: "border-box",
                    }}
                  >
                    {moment(convertUTCToLocalTime(job.creationDate)).format(
                      "ddd, MMM D YYYY, HH:mm:ss",
                    )}
                    {job.completionDate &&
                      ` => ${moment(convertUTCToLocalTime(job.completionDate)).format(
                        "ddd, MMM D YYYY, HH:mm:ss",
                      )}`}
                  </Typography>
                </StepLabelRow>
                <StepLabelRow mt={0.5}>{job.outputId}</StepLabelRow>
                <StepLabelRow py={1}>
                  <Tooltip title={t("study.copyJobId")}>
                    <ContentCopyIcon onClick={() => copyId(job.id)} sx={iconStyle} />
                  </Tooltip>
                  <LaunchJobLogView job={job} logButton logErrorButton />
                  {!outputsLoading && canDisplayDigest(job) && (
                    <Tooltip title="Digest">
                      <EqualizerIcon
                        onClick={() => setDialogState({ type: "digest", job })}
                        sx={iconStyle}
                      />
                    </Tooltip>
                  )}
                  {job.status === "running" && (
                    <CancelContainer>
                      <LinearProgressWithLabel
                        value={jobsProgress[job.id]}
                        tooltip="Progression"
                        sx={{ width: "30%" }}
                      />
                      <Tooltip title={t("study.killStudy")}>
                        <BlockIcon
                          onClick={() => setDialogState({ type: "killJob", job })}
                          sx={{
                            ...iconStyle,
                            color: "error.light",
                            "&:hover": { color: "error.dark" },
                          }}
                        />
                      </Tooltip>
                    </CancelContainer>
                  )}
                </StepLabelRow>
              </StepLabelRoot>
            </StepLabel>
          </Step>
        ))}
      </Stepper>
      {dialogState.type === "killJob" && (
        <ConfirmationDialog
          open
          alert="warning"
          onConfirm={() => killTask(dialogState.job.id)}
          onCancel={closeDialog}
        >
          {t("study.question.killJob")}
        </ConfirmationDialog>
      )}
      {dialogState.type === "digest" && (
        <DigestDialog
          open
          studyId={dialogState.job.studyId}
          outputId={dialogState.job.outputId}
          onOk={closeDialog}
        />
      )}
    </JobRoot>
  );
}

export default JobStepper;
