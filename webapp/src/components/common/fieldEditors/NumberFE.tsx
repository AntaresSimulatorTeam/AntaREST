import { TextField, TextFieldProps } from "@mui/material";
import * as RA from "ramda-adjunct";
import reactHookFormSupport from "../../../hoc/reactHookFormSupport";

export type NumberFEProps = {
  value?: number;
  defaultValue?: number;
} & Omit<TextFieldProps, "type" | "value" | "defaultValue">;

function NumberFE(props: NumberFEProps) {
  return <TextField {...props} type="number" />;
}

export default reactHookFormSupport({
  defaultValue: "" as unknown as number,
  // Returning empty string allow to type negative number
  setValueAs: (v) => (v === "" ? "" : Number(v)),
  preValidate: RA.isNumber,
})(NumberFE);
