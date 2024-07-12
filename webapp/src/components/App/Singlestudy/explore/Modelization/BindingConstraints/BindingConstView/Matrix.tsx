import { useTranslation } from "react-i18next";
import { MatrixStats, StudyMetadata } from "../../../../../../../common/types";
import MatrixInput from "../../../../../../common/MatrixInput";
import { Operator } from "./utils";
import SplitView from "../../../../../../common/SplitView";
import { Box, Button } from "@mui/material";
import BasicDialog, {
  BasicDialogProps,
} from "../../../../../../common/dialogs/BasicDialog";

interface Props {
  study: StudyMetadata;
  operator: Operator;
  constraintId: string;
  open: boolean;
  onClose: () => void;
}

// TODO rename MatrixDialog or ConstraintMatrixDialog
function Matrix({ study, operator, constraintId, open, onClose }: Props) {
  const { t } = useTranslation();
  const dialogProps: BasicDialogProps = {
    open,
    onClose,
    actions: (
      <Button onClick={onClose} color="primary" variant="outlined" size="small">
        {t("global.close")}
      </Button>
    ),
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <BasicDialog
      contentProps={{
        sx: { p: 1, height: "95vh" },
      }}
      fullWidth
      maxWidth="xl"
      {...dialogProps}
    >
      {Number(study.version) >= 870 ? (
        <>
          {operator === "less" && (
            <MatrixInput
              study={study}
              title={t("study.modelization.bindingConst.timeSeries.less")}
              url={`input/bindingconstraints/${constraintId}_lt`}
              computStats={MatrixStats.NOCOL}
            />
          )}
          {operator === "equal" && (
            <MatrixInput
              study={study}
              title={t("study.modelization.bindingConst.timeSeries.equal")}
              url={`input/bindingconstraints/${constraintId}_eq`}
              computStats={MatrixStats.NOCOL}
            />
          )}
          {operator === "greater" && (
            <MatrixInput
              study={study}
              title={t("study.modelization.bindingConst.timeSeries.greater")}
              url={`input/bindingconstraints/${constraintId}_gt`}
              computStats={MatrixStats.NOCOL}
            />
          )}
          {operator === "both" && (
            <SplitView id="binding-constraints-matrix" sizes={[50, 50]}>
              <Box sx={{ px: 2 }}>
                <MatrixInput
                  study={study}
                  title={t("study.modelization.bindingConst.timeSeries.less")}
                  url={`input/bindingconstraints/${constraintId}_lt`}
                  computStats={MatrixStats.NOCOL}
                />
              </Box>
              <Box sx={{ px: 2 }}>
                <MatrixInput
                  study={study}
                  title={t(
                    "study.modelization.bindingConst.timeSeries.greater",
                  )}
                  url={`input/bindingconstraints/${constraintId}_gt`}
                  computStats={MatrixStats.NOCOL}
                />
              </Box>
            </SplitView>
          )}
        </>
      ) : (
        <MatrixInput
          study={study}
          title={t("global.matrix")}
          url={`input/bindingconstraints/${constraintId}`}
          columnsNames={["<", ">", "="]}
          computStats={MatrixStats.NOCOL}
        />
      )}
    </BasicDialog>
  );
}

export default Matrix;
