/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import { useEffect, useState, Children } from "react";
import Split, { type SplitProps } from "react-split";
import { Box } from "@mui/material";
import storage from "../../../services/utils/localStorage";
import "./style.css";

export interface SplitViewProps {
  id: string;
  children: React.ReactNode[];
  direction?: SplitProps["direction"];
  sizes?: SplitProps["sizes"];
  gutterSize?: SplitProps["gutterSize"];
}

/**
 * Renders a resizable split view layout, configurable for both horizontal and vertical directions.
 * Uses localStorage to persist and retrieve the last known sizes of the split panes, using the ID.
 *
 * @example
 * <SplitView id="main-split" direction="vertical" sizes={[30, 70]}>
 *   <ComponentOne />
 *   <ComponentTwo />
 * </SplitView>
 *
 * @param props - The component props.
 * @param props.id - Identifier to uniquely store the sizes of the panes.
 * @param props.children - Child components to be rendered within the split views.
 * @param [props.direction=horizontal] - The orientation of the split view ("horizontal" or "vertical").
 * @param [props.sizes] - Initial sizes of each view in percentages. The array must sum to 100 and match the number of children.
 * @param [props.gutterSize=3] - The size of the gutter between split views.
 * @returns A React component displaying a split layout view with resizable panes.
 */
function SplitView({
  id,
  children,
  direction = "horizontal",
  sizes,
  gutterSize = 3,
}: SplitViewProps) {
  const numberOfChildren = Children.count(children);
  const defaultSizes = Array(numberOfChildren).fill(100 / numberOfChildren);
  const localStorageKey = `splitSizes.${id}.${direction}`;

  const [activeSizes, setActiveSizes] = useState<SplitProps["sizes"]>(() => {
    const savedSizes = storage.getItem(localStorageKey) as number[];
    return savedSizes ?? (sizes || defaultSizes);
  });

  useEffect(() => {
    // Update localStorage whenever activeSizes change.
    storage.setItem(localStorageKey, activeSizes);
  }, [activeSizes, localStorageKey]);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      sx={{
        height: 1,
        width: 1,
        overflow: "auto",
      }}
    >
      <Split
        key={direction} // Force re-render when direction changes.
        className="split"
        direction={direction}
        sizes={activeSizes ?? defaultSizes}
        onDragEnd={setActiveSizes} // Update sizes on drag end.
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
