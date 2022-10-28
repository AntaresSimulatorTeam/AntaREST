import { useMemo } from "react";
import { FieldPath } from "react-hook-form";
import { useTranslation } from "react-i18next";
import SelectFE from "../../../../common/fieldEditors/SelectFE";
import Fieldset from "../../../../common/Fieldset";
import { ControlPlus } from "../../../../common/Form";
import { FilteringType } from "./types";

interface FilterFieldValues {
  filterSynthesis: Array<FilteringType>;
  filterByYear: Array<FilteringType>;
}

interface Props<T extends FilterFieldValues> {
  onAutoSubmit: (name: string, selection: string) => void;
  control: ControlPlus<T>;
}

function OutputFilters<T extends FilterFieldValues>(props: Props<T>) {
  const { onAutoSubmit, control } = props;
  const [t] = useTranslation();

  const filterOptions = useMemo(
    () =>
      ["hourly", "daily", "weekly", "monthly", "annual"].map((item) => ({
        label: t(`global.time.${item}`),
        value: item,
      })),
    [t]
  );

  const renderFilter = (filterName: FieldPath<T>) => (
    <SelectFE
      name={filterName}
      multiple
      options={filterOptions}
      label={t(`study.modelization.nodeProperties.${filterName}`)}
      control={control}
      rules={{
        onAutoSubmit: (value) => {
          const selection = value
            ? (value as Array<string>).filter((val) => val !== "")
            : [];
          onAutoSubmit(filterName, selection.join(", "));
        },
      }}
    />
  );

  return (
    <Fieldset legend={t("study.modelization.nodeProperties.outputFilter")}>
      {renderFilter("filterSynthesis" as FieldPath<T>)}
      {renderFilter("filterByYear" as FieldPath<T>)}
    </Fieldset>
  );
}

export default OutputFilters;
