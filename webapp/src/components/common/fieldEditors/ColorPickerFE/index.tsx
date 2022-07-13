import { Box, TextField, TextFieldProps, InputAdornment } from "@mui/material";
import { ChangeEvent, forwardRef, useRef, useState } from "react";
import { ColorResult, SketchPicker } from "react-color";
import { useTranslation } from "react-i18next";
import SquareRoundedIcon from "@mui/icons-material/SquareRounded";
import { useClickAway, useKey, useUpdateEffect } from "react-use";
import { rgbToString, stringToRGB } from "./utils";
import { mergeSxProp } from "../../../../utils/muiUtils";
import { composeRefs } from "../../../../utils/reactUtils";

export type ColorPickerFEProps = Omit<
  TextFieldProps,
  "type" | "defaultChecked"
> & {
  value?: string; // Format: R,G,B - ex: "255,255,255"
  defaultValue?: string;
};

const ColorPickerFE = forwardRef((props: ColorPickerFEProps, ref) => {
  const { value, defaultValue, onChange, sx, ...textFieldProps } = props;
  const [currentColor, setCurrentColor] = useState(defaultValue || value || "");
  const [isPickerOpen, setIsPickerOpen] = useState(false);
  const internalRef = useRef<HTMLInputElement>();
  const pickerWrapperRef = useRef(null);
  const { t } = useTranslation();

  useUpdateEffect(() => {
    setCurrentColor(value ?? "");
  }, [value]);

  useClickAway(pickerWrapperRef, () => {
    setIsPickerOpen(false);
  });

  useKey("Escape", () => setIsPickerOpen(false));

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleChange = ({ hex, rgb }: ColorResult) => {
    setCurrentColor(
      ["transparent", "#0000"].includes(hex) ? "" : rgbToString(rgb)
    );
  };

  const handleChangeComplete = () => {
    onChange?.({
      target: internalRef.current,
      type: "change",
    } as ChangeEvent<HTMLInputElement>);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      sx={mergeSxProp(
        {
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          position: "relative",
        },
        sx
      )}
    >
      <TextField
        label={t("global.color")}
        variant="filled"
        {...textFieldProps}
        sx={{ mx: 1 }}
        value={currentColor}
        placeholder={currentColor}
        inputRef={composeRefs(ref, internalRef)}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SquareRoundedIcon
                sx={{
                  color: currentColor ? `rgb(${currentColor})` : "transparent",
                }}
              />
            </InputAdornment>
          ),
        }}
        onClick={() => setIsPickerOpen(true)}
      />
      {isPickerOpen && (
        <Box
          sx={{
            position: "absolute",
            top: "calc(100% + 8px)",
            zIndex: 1000,
          }}
          ref={pickerWrapperRef}
        >
          <SketchPicker
            color={currentColor && stringToRGB(currentColor)}
            onChange={handleChange}
            onChangeComplete={handleChangeComplete}
            disableAlpha
          />
        </Box>
      )}
    </Box>
  );
});

ColorPickerFE.displayName = "ColorPicker";

export default ColorPickerFE;
