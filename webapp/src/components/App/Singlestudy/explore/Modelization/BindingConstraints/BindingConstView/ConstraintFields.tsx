import Fieldset from "../../../../../../common/Fieldset";
import SelectFE from "../../../../../../common/fieldEditors/SelectFE";
import StringFE from "../../../../../../common/fieldEditors/StringFE";
import { useTranslation } from "react-i18next";
import {
  BindingConstraint,
  OPERATORS,
  OUTPUT_FILTERS,
  TIME_STEPS,
} from "./utils";
import { useFormContextPlus } from "../../../../../../common/Form";
import { useMemo } from "react";
import { StudyMetadata } from "../../../../../../../common/types";
import SwitchFE from "../../../../../../common/fieldEditors/SwitchFE";
import { validateString } from "../../../../../../../utils/validationUtils";

interface Props {
  study: StudyMetadata;
}

function Fields({ study }: Props) {
  const { t } = useTranslation();
  const { control } = useFormContextPlus<BindingConstraint>();

  const outputFilterOptions = useMemo(
    () =>
      OUTPUT_FILTERS.map((filter) => ({
        label: t(`global.time.${filter}`),
        value: filter,
      })),
    [t],
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <Fieldset legend={t("global.general")} fieldWidth={200} sx={{ pb: 2 }}>
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
          options={TIME_STEPS}
          control={control}
        />
        <SelectFE
          name="operator"
          label={t("study.modelization.bindingConst.operator")}
          size="small"
          variant="outlined"
          options={OPERATORS}
          control={control}
        />
        <SwitchFE
          name="enabled"
          label={t("study.modelization.bindingConst.enabled")}
          control={control}
        />
      </Fieldset>

      {study.version >= "840" && (
        <Fieldset legend={t("study.outputFilters")} sx={{ pb: 2 }}>
          <SelectFE
            name="filterYearByYear"
            label={t("study.outputFilters.filterByYear")}
            size="small"
            variant="outlined"
            options={outputFilterOptions}
            multiple
            control={control}
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
        </Fieldset>
      )}
    </>
  );
}

export default Fields;
