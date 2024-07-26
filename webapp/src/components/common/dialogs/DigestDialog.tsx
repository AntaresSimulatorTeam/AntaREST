import { Skeleton } from "@mui/material";
import OkDialog, { OkDialogProps } from "./OkDialog";
import EditableMatrix from "../EditableMatrix";
import UsePromiseCond from "../utils/UsePromiseCond";
import type { LaunchJob } from "../../../common/types";
import { getStudyData } from "../../../services/api/study";
import usePromise from "../../../hooks/usePromise";
import { useTranslation } from "react-i18next";
import { AxiosError } from "axios";
import EmptyView from "../page/SimpleContent";
import SearchOffIcon from "@mui/icons-material/SearchOff";

// TODO: redesign DataViewerDialog to use path, then remove this component

export interface DigestDialogProps
  extends Pick<OkDialogProps, "open" | "onOk" | "onClose"> {
  studyId: LaunchJob["studyId"];
  outputId: LaunchJob["outputId"];
}

function DigestDialog({
  studyId,
  outputId,
  ...dialogProps
}: DigestDialogProps) {
  const { t } = useTranslation();

  const synthesisRes = usePromise(
    () =>
      getStudyData(studyId, `output/${outputId}/economy/mc-all/grid/digest`),
    {
      deps: [studyId, outputId],
    },
  );

  return (
    <OkDialog
      {...dialogProps}
      title="Digest"
      okButtonText={t("global.close")}
      fullScreen
      sx={{ m: 5 }}
    >
      <UsePromiseCond
        response={synthesisRes}
        ifPending={() => <Skeleton sx={{ height: 1, transform: "none" }} />}
        ifRejected={(error) => {
          if (error instanceof AxiosError && error.response?.status === 404) {
            return (
              <EmptyView
                title={t("global.error.fileNotFound")}
                icon={SearchOffIcon}
              />
            );
          }
          return <EmptyView title={error?.toString()} />;
        }}
        ifResolved={(matrix) =>
          matrix && (
            <EditableMatrix
              matrix={matrix}
              columnsNames={matrix.columns}
              matrixTime={false}
              readOnly
            />
          )
        }
      />
    </OkDialog>
  );
}

export default DigestDialog;
