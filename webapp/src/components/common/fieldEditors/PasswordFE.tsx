import { TextField, TextFieldProps } from "@mui/material";
import reactHookFormSupport from "../../../hoc/reactHookFormSupport";

export type PasswordFEProps = {
  value?: string;
  defaultValue?: string;
} & Omit<TextFieldProps, "type" | "value" | "defaultValue">;

function PasswordFE(props: PasswordFEProps) {
  return <TextField {...props} type="password" />;
}

export default reactHookFormSupport({ defaultValue: "" })(PasswordFE);
