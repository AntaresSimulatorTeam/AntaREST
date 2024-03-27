import {
  BindingConstraint,
  OPERATORS,
  OUTPUT_FILTERS,
  TIME_STEPS,
} from "./utils";

import Fieldset from "../../../../../../common/Fieldset";
import SelectFE from "../../../../../../common/fieldEditors/SelectFE";
import StringFE from "../../../../../../common/fieldEditors/StringFE";
import { StudyMetadata } from "../../../../../../../common/types";
import SwitchFE from "../../../../../../common/fieldEditors/SwitchFE";
import { useFormContextPlus } from "../../../../../../common/Form";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { validateString } from "../../../../../../../utils/validationUtils";
import Matrix from "./Matrix";
import { Box } from "@mui/material";

interface Props {
  study: StudyMetadata;
  constraintId: string;
  isMatrixOpen: boolean;
  onCloseMatrix: VoidFunction;
}

function Fields({ study, constraintId, isMatrixOpen, onCloseMatrix }: Props) {
  const { t } = useTranslation();
  const { control, getValues } = useFormContextPlus<BindingConstraint>();
  const currentOperator = getValues("operator");

  const outputFilterOptions = useMemo(
    () =>
      OUTPUT_FILTERS.map((filter) => ({
        label: t(`global.time.${filter}`),
        value: filter,
      })),
    [t],
  );

  const operatorOptions = useMemo(
    () =>
      OPERATORS.map((operator) => ({
        label: t(`study.modelization.bindingConst.operator.${operator}`),
        value: operator,
      })),
    [t],
  );

  const timeStepOptions = useMemo(
    () =>
      TIME_STEPS.map((timeStep) => ({
        label: t(`global.time.${timeStep}`),
        value: timeStep,
      })),
    [t],
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <Fieldset
        fieldWidth={200}
        sx={{ py: 1, display: "flex", flexWrap: "wrap" }}
      >
        <StringFE
          disabled
          name="name"
          label={t("global.name")}
          size="small"
          control={control}
          rules={{ validate: (v) => validateString(v) }}
          sx={{ m: 0 }} // TODO: Remove when updating MUI Theme
        />
        <StringFE
          name="group"
          label={t("global.group")}
          size="small"
          control={control}
          sx={{ m: 0 }} // TODO: Remove when updating MUI Theme
        />
        <StringFE
          name="comments"
          label={t("study.modelization.bindingConst.comments")}
          size="small"
          control={control}
          sx={{ m: 0 }} // TODO: Remove when updating MUI Theme
        />
        <SelectFE
          name="timeStep"
          label={t("study.modelization.bindingConst.type")}
          size="small"
          variant="outlined"
          options={timeStepOptions}
          control={control}
        />
        <SelectFE
          name="operator"
          label={t("study.modelization.bindingConst.operator")}
          size="small"
          variant="outlined"
          options={operatorOptions}
          control={control}
        />
        <SwitchFE
          name="enabled"
          label={t("study.modelization.bindingConst.enabled")}
          control={control}
        />

        {study.version >= "840" && (
          <Box sx={{ width: 1 }}>
            <SelectFE
              name="filterYearByYear"
              label={t("study.outputFilters.filterByYear")}
              size="small"
              variant="outlined"
              options={outputFilterOptions}
              multiple
              control={control}
              sx={{ mr: 2 }}
            />
            <SelectFE
              name="filterSynthesis"
              label={t("study.outputFilters.filterSynthesis")}
              size="small"
              variant="outlined"
              options={outputFilterOptions}
              multiple
              control={control}
            />
          </Box>
        )}
      </Fieldset>

      {isMatrixOpen && (
        <Matrix
          study={study}
          constraintId={constraintId}
          operator={currentOperator}
          open={isMatrixOpen}
          onClose={onCloseMatrix}
        />
      )}
    </>
  );
}

export default Fields;
