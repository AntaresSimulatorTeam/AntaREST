import { SelectChangeEvent } from "@mui/material";
import * as RA from "ramda-adjunct";
import reactHookFormSupport from "../../../hoc/reactHookFormSupport";
import SelectFE, { SelectFEProps } from "./SelectFE";

interface BooleanFEProps extends Omit<SelectFEProps, "options" | "multiple"> {
  defaultValue?: boolean;
  value?: boolean;
  trueText?: string;
  falseText?: string;
}

function toValidValue(value?: boolean) {
  if (RA.isBoolean(value)) {
    return value ? "true" : "false";
  }
  return value;
}

function toValidEvent<
  T extends
    | SelectChangeEvent<unknown>
    | React.FocusEvent<HTMLInputElement | HTMLTextAreaElement>
>(event: T): T {
  return {
    ...event,
    target: {
      ...event.target,
      value: event.target.value === "true",
    },
  } as T;
}

function BooleanFE(props: BooleanFEProps) {
  const {
    defaultValue,
    value,
    trueText,
    falseText,
    onChange,
    onBlur,
    inputRef,
    ...rest
  } = props;

  return (
    <SelectFE
      {...rest}
      onBlur={(event) => {
        onBlur?.(toValidEvent(event));
      }}
      onChange={(event, child) => {
        onChange?.(toValidEvent(event), child);
      }}
      defaultValue={toValidValue(defaultValue)}
      value={toValidValue(value)}
      options={[
        // TODO i18n
        { label: trueText || "True", value: "true" },
        { label: falseText || "False", value: "false" },
      ]}
      inputRef={inputRef}
    />
  );
}

export default reactHookFormSupport({ defaultValue: false })(BooleanFE);
