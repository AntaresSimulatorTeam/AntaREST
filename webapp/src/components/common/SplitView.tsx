import React from "react";
import Split, { SplitProps } from "react-split";
import { v4 as uuidv4 } from "uuid";
import { Box, SxProps, Theme } from "@mui/material";

export interface SplitViewProps {
  children: React.ReactNode[];
  direction?: SplitProps["direction"];
  sizes: SplitProps["sizes"];
  gutterSize?: SplitProps["gutterSize"];
  snapOffset?: SplitProps["snapOffset"];
  sx?: SxProps<Theme>;
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
  direction = "horizontal",
  sizes = [50, 50],
  gutterSize = 4,
  snapOffset = 0,
  sx,
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
        key={`split-${direction}`} // force re-render when direction changes.
        className="split"
        direction={direction}
        sizes={sizes.length === numberOfChildren ? sizes : defaultSizes} // sizes array must sum up to 100 and match the number of children.
        gutterSize={gutterSize}
        snapOffset={snapOffset}
        style={{
          display: "flex",
          flexDirection: direction === "horizontal" ? "row" : "column",
        }}
      >
        {children.map((child) => (
          <Box
            key={uuidv4()}
            sx={{
              height: 1,
              width: 1,
              overflow: "hidden",
              ...sx,
            }}
          >
            {child}
          </Box>
        ))}
      </Split>
    </Box>
  );
}

export default SplitView;
