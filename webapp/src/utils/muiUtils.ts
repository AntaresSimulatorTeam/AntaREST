import { SxProps, Theme } from "@mui/material";

export function mergeSxProp(
  target: SxProps<Theme> = {},
  source: SxProps<Theme> = [],
): SxProps<Theme> {
  // https://mui.com/system/getting-started/the-sx-prop/#passing-the-sx-prop
  return [target, ...(Array.isArray(source) ? source : [source])];
}
