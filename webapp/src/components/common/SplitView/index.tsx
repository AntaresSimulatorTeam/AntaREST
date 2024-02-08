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
 * Renders a resizable split view layout. It can be configured
 * for both horizontal and vertical directions.
 * @see {@link SplitViewProps} for the properties it accepts.
 *
 * @example
 * <SplitView direction="vertical" sizes={[30, 70]}>
 *   <ComponentOne />
 *   <ComponentTwo />
 * </SplitView>
 */
function SplitView({
  children,
  direction,
  sizes,
  gutterSize = 4,
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
