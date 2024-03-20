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
      <Fieldset legend={t("global.general")} fieldWidth={180}>
        <StringFE
          disabled
          name="name"
          label="Name"
          size="small"
          control={control}
          sx={{ m: 0 }} // TODO: Remove when updating MUI Theme
        />
        <StringFE
          name="group"
          label="Group"
          size="small"
          control={control}
          sx={{ m: 0 }} // TODO: Remove when updating MUI Theme
        />
        <StringFE
          name="comments"
          label="Comments"
          size="small"
          control={control}
          sx={{ m: 0 }} // TODO: Remove when updating MUI Theme
        />
        <SelectFE
          name="time_step"
          label="Type"
          size="small"
          variant="outlined"
          options={TIME_STEPS}
          control={control}
        />
        <SelectFE
          name="operator"
          label="Operator"
          size="small"
          variant="outlined"
          options={OPERATORS}
          control={control}
        />
        <SwitchFE name="enabled" label="Enabled" control={control} />
      </Fieldset>

      {study.version >= "840" && (
        <Fieldset legend={t("study.outputFilters")}>
          <SelectFE
            name="filter_year_by_year"
            label={t("study.outputFilters.filterByYear")}
            size="small"
            variant="outlined"
            options={outputFilterOptions}
            multiple
            control={control}
          />
          <SelectFE
            name="filter_synthesis"
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
