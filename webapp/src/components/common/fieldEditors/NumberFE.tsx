import { TextField, TextFieldProps } from "@mui/material";
import withReactHookFormSupport from "../../../hoc/reactHookFormSupport";

export type NumberFEProps = {
  value?: number;
  defaultValue?: number;
} & Omit<TextFieldProps, "type" | "value" | "defaultValue">;

function NumberFE(props: NumberFEProps) {
  return <TextField {...props} type="number" />;
}

export default withReactHookFormSupport({
  defaultValue: 0,
  setValueAs: Number,
})(NumberFE);
