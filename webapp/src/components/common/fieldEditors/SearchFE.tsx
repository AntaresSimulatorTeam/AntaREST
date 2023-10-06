import { useState } from "react";
import { InputAdornment } from "@mui/material";
import ClearIcon from "@mui/icons-material/Clear";
import IconButton from "@mui/material/IconButton";
import SearchIcon from "@mui/icons-material/Search";
import { useTranslation } from "react-i18next";
import clsx from "clsx";
import StringFE, { StringFEProps } from "./StringFE";

export interface SearchFE extends Omit<StringFEProps, "placeholder" | "label"> {
  InputProps?: Omit<StringFEProps["InputProps"], "startAdornment" | "endAdornment" | "value">;
  onSearchValueChange?: (value: string) => void;
  useLabel?: boolean;
}

function SearchFE(props: SearchFE) {
  const {
    onSearchValueChange,
    onChange,
    InputProps,
    useLabel,
    className,
    ...rest
  } = props;
  const { t } = useTranslation();
  const placeholderOrLabel = {
    [useLabel ? "label" : "placeholder"]: t("global.search"),
  };
  const [value, setValue] = useState("");

  return (
    <StringFE
      {...rest}
      {...placeholderOrLabel}
      className={clsx("SearchFE", className)}
      InputProps={{
        ...InputProps,
        startAdornment: (
          <InputAdornment position="start">
            <SearchIcon />
          </InputAdornment>
        ),
        endAdornment: (
          <InputAdornment position="end">
            <IconButton
              aria-label="Clear"
              size="small"
              onClick={() => {
                setValue("");
                onSearchValueChange?.("");
              }}
            >
              <ClearIcon />
            </IconButton>
          </InputAdornment>
        ),
      }}
      value={value}
      onChange={(event) => {
        onChange?.(event);
        setValue(event.target.value);
        onSearchValueChange?.(event.target.value);
      }}
    />
  );
}

export default SearchFE;
