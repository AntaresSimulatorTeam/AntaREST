import { TextField, TextFieldProps } from "@mui/material";
import reactHookFormSupport from "../../../hoc/reactHookFormSupport";

export type StringFEProps = {
  value?: string;
  defaultValue?: string;
} & Omit<TextFieldProps, "type" | "value" | "defaultValue">;

function StringFE(props: StringFEProps) {
  return <TextField {...props} type="text" />;
}

export default reactHookFormSupport({ defaultValue: "" })(StringFE);
