import { useTranslation } from "react-i18next";
import { MatrixStats, StudyMetadata } from "../../../../../../../common/types";
import MatrixInput from "../../../../../../common/MatrixInput";
import { Operator, TimeStep } from "./utils";
import SplitView from "../../../../../../common/SplitView";

interface Props {
  study: StudyMetadata;
  operator: Operator;
  timeStep: TimeStep;
  constraintId: string;
}

function Matrix({ study, operator, timeStep, constraintId }: Props) {
  const { t } = useTranslation();
  const studyVersion = Number(study.version);

  if (studyVersion >= 870) {
    return (
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
          <SplitView direction="horizontal" sizes={[50, 50]}>
            <MatrixInput
              study={study}
              title={t("study.modelization.bindingConst.timeSeries.less")}
              url={`input/bindingconstraints/${constraintId}_lt`}
              computStats={MatrixStats.NOCOL}
            />

            <MatrixInput
              study={study}
              title={t("study.modelization.bindingConst.timeSeries.greater")}
              url={`input/bindingconstraints/${constraintId}_gt`}
              computStats={MatrixStats.NOCOL}
            />
          </SplitView>
        )}
      </>
    );
  }

  // Fallback for versions below 8.7
  return (
    <MatrixInput
      study={study}
      title={t("global.matrix")}
      url={`input/bindingconstraints/${constraintId}`}
      columnsNames={["<", ">", "="]}
      computStats={MatrixStats.NOCOL}
    />
  );
}

export default Matrix;
