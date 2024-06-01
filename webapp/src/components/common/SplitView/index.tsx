import React from "react";
import Split, { SplitProps } from "react-split";
import { Box } from "@mui/material";
import "./style.css";

export interface SplitViewProps {
  children: React.ReactNode[];
  direction?: SplitProps["direction"];
  sizes?: SplitProps["sizes"];
  gutterSize?: SplitProps["gutterSize"];
}

/**
 * Renders a resizable split view layout, configurable for both horizontal and vertical directions.
 *
 * @see {@link SplitViewProps} for the properties it accepts.
 *
 * @example
 * <SplitView direction="vertical" sizes={[30, 70]}>
 *   <ComponentOne />
 *   <ComponentTwo />
 * </SplitView>
 *
 * @param props - The component props.
 * @param props.children - Child components to be rendered within the split views.
 * @param props.direction - The orientation of the split view ("horizontal" or "vertical").
 * @param props.sizes - Initial sizes of each view in percentages. The array must sum to 100 and match the number of children.
 * @param props.gutterSize - The size of the gutter between split views. Defaults to 4.
 * @returns A React component displaying a split layout view with resizable panes.
 */
function SplitView({
  children,
  direction = "horizontal",
  sizes,
  gutterSize = 3,
}: SplitViewProps) {
  const numberOfChildren = React.Children.count(children);
  const defaultSizes = Array(numberOfChildren).fill(100 / numberOfChildren);

  return (
    <Box
      sx={{
        height: 1,
        width: 1,
        overflow: "auto",
      }}
    >
      <Split
        key={direction} // force re-render when direction changes.
        className="split"
        direction={direction}
        sizes={sizes?.length === numberOfChildren ? sizes : defaultSizes} // sizes array must sum up to 100 and match the number of children.
        gutterSize={gutterSize}
        style={{
          display: "flex",
          flexDirection: direction === "horizontal" ? "row" : "column",
        }}
      >
        {children}
      </Split>
    </Box>
  );
}

export default SplitView;
