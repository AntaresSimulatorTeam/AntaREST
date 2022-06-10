import {
  Box,
  Button,
  TextField,
  TextFieldProps,
  InputAdornment,
  setRef,
} from "@mui/material";
import { ChangeEvent, forwardRef, useEffect, useRef, useState } from "react";
import { ColorResult, SketchPicker } from "react-color";
import { useTranslation } from "react-i18next";
import CancelRoundedIcon from "@mui/icons-material/CancelRounded";
import SquareRoundedIcon from "@mui/icons-material/SquareRounded";
import { RGBToString, stringToRGB } from "./utils";

interface Props {
  currentColor?: Partial<ColorResult["rgb"]>;
}

const ColorPicker = forwardRef((props: Props & TextFieldProps, ref) => {
  const { currentColor, onChange, ...other } = props;
  const [color, setColor] = useState<string>(RGBToString(currentColor || {}));
  const [t] = useTranslation();
  const [isPickerOpen, setIsPickerOpen] = useState(false);
  const internalRef = useRef<HTMLTextAreaElement>();

  useEffect(() => {
    if (color && internalRef.current && onChange) {
      onChange({
        target: internalRef.current,
      } as ChangeEvent<HTMLTextAreaElement>);
    }
  }, [color, onChange]);

  useEffect(() => {
    if (currentColor) {
      setColor(RGBToString(currentColor));
    }
  }, [currentColor]);

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        position: "relative",
      }}
    >
      <TextField
        sx={{ mx: 1 }}
        label={t("global.color")}
        variant="filled"
        placeholder={color}
        inputRef={(instance) => {
          setRef(ref, instance);
          setRef(internalRef, instance);
        }}
        value={color}
        InputLabelProps={
          // Allow to show placeholder when field is empty
          currentColor !== undefined ? { shrink: true } : {}
        }
        {...other}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SquareRoundedIcon
                sx={{
                  color: color
                    ? `rgb(${color})` // `rgb(${color.r},${color.g},${color.b})`
                    : "#0000",
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
        >
          <SketchPicker
            color={stringToRGB(color)}
            onChangeComplete={(
              color: ColorResult,
              ev: ChangeEvent<HTMLInputElement>
            ) => {
              setColor(RGBToString(color.rgb));
            }}
          />
          <Button
            variant="text"
            onClick={() => setIsPickerOpen(false)}
            sx={{
              minWidth: 0,
              minHeight: 0,
              width: "auto",
              height: "auto",
              p: 0,
              position: "absolute",
              top: "-8px",
              right: "-8px",
              zIndex: 10000,
              color: "black",
            }}
          >
            <CancelRoundedIcon />
          </Button>
        </Box>
      )}
    </Box>
  );
});

export default ColorPicker;
