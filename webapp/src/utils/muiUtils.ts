import { SxProps, Theme } from "@mui/material";
import { SystemStyleObject } from "@mui/system";

export function mergeSxProp(
  style: SystemStyleObject<Theme>,
  sxProp: SxProps<Theme> = []
): SxProps<Theme> {
  // https://mui.com/system/the-sx-prop/#passing-sx-prop
  return [style, ...(Array.isArray(sxProp) ? sxProp : [sxProp])];
}
