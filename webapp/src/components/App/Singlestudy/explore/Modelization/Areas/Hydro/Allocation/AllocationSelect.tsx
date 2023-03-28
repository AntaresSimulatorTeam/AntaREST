import { Box } from "@mui/material";
import { t } from "i18next";
import { memo, useMemo } from "react";
import { Area } from "../../../../../../../../common/types";
import SelectFE from "../../../../../../../common/fieldEditors/SelectFE";

interface Props {
  filteredAreas: Array<Area & { id: string }>;
  appendField: (obj: { areaId: string; coefficient: number }) => void;
}

export default memo(function AllocationSelect({
  filteredAreas,
  appendField,
}: Props) {
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
    <Box
      sx={{
        display: "flex",
        flexDirection: "row",
        alignItems: "center",
      }}
    >
      {filteredAreas.length > 0 && (
        <SelectFE
          label={t("study.modelization.hydro.allocation.select")}
          options={options}
          onChange={(e) => {
            appendField({ areaId: e.target.value as string, coefficient: 0 });
          }}
          size="small"
          sx={{ minWidth: 180 }}
        />
      )}
    </Box>
  );
});
