import { Skeleton } from "@mui/material";
import OkDialog, {
  OkDialogProps,
} from "../../../../../common/dialogs/OkDialog";
import EditableMatrix from "../../../../../common/EditableMatrix";
import UsePromiseCond from "../../../../../common/utils/UsePromiseCond";
import type { LaunchJob } from "../../../../../../common/types";
import { getStudyData } from "../../../../../../services/api/study";
import usePromise from "../../../../../../hooks/usePromise";
import { useTranslation } from "react-i18next";

interface Props extends Pick<OkDialogProps, "open" | "onOk" | "onClose"> {
  studyId: LaunchJob["studyId"];
  outputId: LaunchJob["outputId"];
}

function DigestDialog({ studyId, outputId, ...dialogProps }: Props) {
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
