import { t } from "i18next";
import { useMemo } from "react";
import { UseFieldArrayAppend } from "react-hook-form";
import { Area } from "../../../../../../../../common/types";
import SelectFE from "../../../../../../../common/fieldEditors/SelectFE";
import { CorrelationFormFields } from "./utils";

interface Props {
  filteredAreas: Array<Area & { id: string }>;
  append: UseFieldArrayAppend<CorrelationFormFields, "correlation">;
}

function CorrelationSelect({ filteredAreas, append }: Props) {
  const options = useMemo(
    () =>
      filteredAreas.map((area) => ({
        label: area.name,
        value: area.id,
      })),
    [filteredAreas]
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return filteredAreas.length > 0 ? (
    <SelectFE
      label={t("study.modelization.hydro.area.add")}
      options={options}
      onChange={(e) => {
        append({ areaId: e.target.value as string, coefficient: 0 });
      }}
      size="small"
      variant="outlined"
      sx={{ width: 200 }}
    />
  ) : null;
}

export default CorrelationSelect;
