import { ColorResult } from "react-color";

export function stringToRGB(color: string): ColorResult["rgb"] | undefined {
  let sColor;
  try {
    sColor = color
      .split(",")
      .map((elm) => parseInt(elm.replace(/\s+/g, ""), 10));
  } catch (e) {
    sColor = undefined;
  }

  if (sColor && sColor.length === 3) {
    return {
      r: sColor[0],
      g: sColor[1],
      b: sColor[2],
    };
  }
  return undefined;
}

export function rgbToString(color: Partial<ColorResult["rgb"]>): string {
  const { r, g, b } = color;
  if (r === undefined || g === undefined || b === undefined) return "";
  return `${r},${g},${b}`;
}
