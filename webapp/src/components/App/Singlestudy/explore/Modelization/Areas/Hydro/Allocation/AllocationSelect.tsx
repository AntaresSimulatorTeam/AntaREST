import { Box } from "@mui/material";
import { t } from "i18next";
import { useMemo } from "react";
import { Area } from "../../../../../../../../common/types";
import SelectFE from "../../../../../../../common/fieldEditors/SelectFE";

interface Props {
  filteredAreas: Array<Area & { id: string }>;
  append: (obj: { areaId: string; coefficient: number }) => void;
}

function AllocationSelect({ filteredAreas, append }: Props) {
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

  return (
    <Box>
      {filteredAreas.length > 0 && (
        <SelectFE
          label={t("study.modelization.hydro.allocation.select")}
          options={options}
          onChange={(e) => {
            append({ areaId: e.target.value as string, coefficient: 0 });
          }}
          size="small"
          variant="outlined"
        />
      )}
    </Box>
  );
}

export default AllocationSelect;
