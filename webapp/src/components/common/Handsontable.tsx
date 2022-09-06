import HotTable, { HotTableProps } from "@handsontable/react";
import { styled } from "@mui/material";
import { registerAllModules } from "handsontable/registry";
import { forwardRef } from "react";
import { SECONDARY_MAIN_COLOR } from "../../theme";

// Register Handsontable's modules
registerAllModules();

const StyledHotTable = styled(HotTable)(() => ({
  "th, td, .handsontableInput": {
    backgroundColor: "#222333 !important",
  },
  "th, td": {
    borderColor: "rgba(255, 255, 255, 0.1) !important",
  },
  "th, td:not(.htDimmed), .handsontableInput": {
    color: "#fff !important",
  },
  th: {
    fontWeight: "bold !important",
  },
  "th.ht__highlight": {
    backgroundColor: `${SECONDARY_MAIN_COLOR}8c !important`,
  },
  "th.ht__active_highlight": {
    backgroundColor: `${SECONDARY_MAIN_COLOR} !important`,
  },
}));

export type HandsontableProps = Omit<HotTableProps, "licenseKey">;

const Handsontable = forwardRef<HotTable, HandsontableProps>((props, ref) => {
  return (
    <StyledHotTable
      licenseKey="non-commercial-and-evaluation"
      {...props}
      ref={ref}
    />
  );
});

Handsontable.displayName = "Handsontable";

export default Handsontable;
