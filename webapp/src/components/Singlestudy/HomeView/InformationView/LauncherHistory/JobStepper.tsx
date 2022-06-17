import Stepper from "@mui/material/Stepper";
import Step from "@mui/material/Step";
import StepLabel from "@mui/material/StepLabel";
import FiberManualRecordIcon from "@mui/icons-material/FiberManualRecord";
import BlockIcon from "@mui/icons-material/Block";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import { StepIconProps, Tooltip, Typography } from "@mui/material";
import moment from "moment";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import { AxiosError } from "axios";
import { JobStatus, LaunchJob } from "../../../../../common/types";
import { convertUTCToLocalTime } from "../../../../../services/utils";
import { killStudy } from "../../../../../services/api/study";
import LaunchJobLogView from "../../../../Tasks/LaunchJobLogView";
import useEnqueueErrorSnackbar from "../../../../../hooks/useEnqueueErrorSnackbar";
import {
  CancelContainer,
  JobRoot,
  QontoConnector,
  QontoStepIconRoot,
  StepLabelRoot,
  StepLabelRow,
} from "./style";
import ConfirmationDialog from "../../../../common/dialogs/ConfirmationDialog";

export const ColorStatus = {
  running: "warning.main",
  pending: "grey.400",
  success: "success.main",
  failed: "error.main",
};

function QontoStepIcon(props: {
  className: string | undefined;
  status: JobStatus;
}) {
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

interface Props {
  jobs: Array<LaunchJob>;
}

export default function VerticalLinearStepper(props: Props) {
  const { jobs } = props;
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [openConfirmationDialog, setOpenConfirmationDialog] =
    useState<boolean>(false);
  const [jobIdKill, setJobIdKill] = useState<string>();

  const openConfirmModal = (jobId: string) => {
    setOpenConfirmationDialog(true);
    setJobIdKill(jobId);
  };

  const killTask = (jobId: string) => {
    (async () => {
      try {
        await killStudy(jobId);
      } catch (e) {
        enqueueErrorSnackbar(t("study.failtokilltask"), e as AxiosError);
      }
      setOpenConfirmationDialog(false);
    })();
  };

  const copyId = (jobId: string): void => {
    try {
      navigator.clipboard.writeText(jobId);
      enqueueSnackbar(t("study.success.jobIdCopy"), {
        variant: "success",
      });
    } catch (e) {
      enqueueErrorSnackbar(t("study.error.jobIdCopy"), e as AxiosError);
    }
  };

  return (
    <JobRoot jobLength={jobs.length}>
      <Stepper
        activeStep={-1}
        orientation="vertical"
        connector={<QontoConnector />}
        sx={{ width: "100%", px: 2, boxSizing: "border-box" }}
      >
        {jobs.map((job, index) => (
          <Step key={job.id}>
            <StepLabel
              StepIconComponent={({ className }: StepIconProps) =>
                QontoStepIcon({ className, status: job.status })
              }
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
                      "ddd, MMM D YYYY, HH:mm:ss"
                    )}
                    {job.completionDate &&
                      ` => ${moment(
                        convertUTCToLocalTime(job.completionDate)
                      ).format("ddd, MMM D YYYY, HH:mm:ss")}`}
                  </Typography>
                </StepLabelRow>
                <StepLabelRow mt={0.5}>{job.outputId}</StepLabelRow>
                <StepLabelRow py={1}>
                  <Tooltip title={t("study.copyJobId") as string}>
                    <ContentCopyIcon
                      onClick={() => copyId(job.id)}
                      sx={{
                        m: 0.5,
                        height: "22px",
                        cursor: "pointer",
                        "&:hover": {
                          color: "action.hover",
                        },
                      }}
                    />
                  </Tooltip>
                  <LaunchJobLogView job={job} logButton logErrorButton />
                  {job.status === "running" && (
                    <CancelContainer>
                      <Tooltip title={t("study.killStudy") as string}>
                        <BlockIcon
                          onClick={() => openConfirmModal(job.id)}
                          sx={{
                            m: 0.5,
                            height: "22px",
                            cursor: "pointer",
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
      {openConfirmationDialog && (
        <ConfirmationDialog
          onCancel={() => setOpenConfirmationDialog(false)}
          onConfirm={() => killTask(jobIdKill as string)}
          alert="warning"
          open
        >
          {t("study.question.killJob")}
        </ConfirmationDialog>
      )}
    </JobRoot>
  );
}
