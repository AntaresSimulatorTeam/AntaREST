import { registerAllModules } from "handsontable/registry";
import HotTable, { HotTableProps } from "@handsontable/react";
import { styled } from "@mui/material";
import { forwardRef } from "react";
import * as RA from "ramda-adjunct";
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

export type HotTableClass = React.ElementRef<HotTable>;

const Handsontable = forwardRef<HotTableClass, HandsontableProps>(
  (props, ref) => {
    ////////////////////////////////////////////////////////////////
    // Event Handlers
    ////////////////////////////////////////////////////////////////

    const handleBeforeChange: HotTableProps["beforeChange"] =
      function beforeChange(this: unknown, changes, ...rest): void {
        changes.filter(Boolean).forEach((cell) => {
          const [, , oldValue, newValue] = cell;
          // Prevent null values for string cells
          if (RA.isString(oldValue) && newValue === null) {
            // eslint-disable-next-line no-param-reassign
            cell[3] = "";
          }
        });
        props.beforeChange?.call(this, changes, ...rest);
      };

    ////////////////////////////////////////////////////////////////
    // JSX
    ////////////////////////////////////////////////////////////////

    return (
      <StyledHotTable
        licenseKey="non-commercial-and-evaluation"
        {...props}
        beforeChange={handleBeforeChange}
        ref={ref}
      />
    );
  },
);

Handsontable.displayName = "Handsontable";

export default Handsontable;
