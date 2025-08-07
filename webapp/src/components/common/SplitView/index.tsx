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

import { Children, useState } from "react";
import Split, { type SplitProps } from "react-split";
import { useUpdateEffect } from "react-use";
import storage from "../../../services/utils/localStorage";
import "./style.css";

export interface SplitViewProps {
  id: string;
  children: React.ReactNode[];
  direction?: SplitProps["direction"];
  sizes?: SplitProps["sizes"];
  minSize?: SplitProps["minSize"];
  gutterSize?: SplitProps["gutterSize"];
}

function isValidSizes(sizes: unknown): sizes is number[] {
  return (
    Array.isArray(sizes) &&
    sizes.every((size) => typeof size === "number") &&
    sizes.reduce((sum, size) => sum + size) === 100
  );
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
 * @param [props.minSize=[150, 150]] - Minimum sizes of the elements, specified as pixel values.
 * @param [props.gutterSize=3] - The size of the gutter between split views.
 * @returns A React component displaying a split layout view with resizable panes.
 */
function SplitView({
  id,
  children,
  direction = "horizontal",
  sizes,
  minSize = [150, 150],
  gutterSize = 3,
}: SplitViewProps) {
  const numberOfChildren = Children.count(children);
  const defaultSizes = Array(numberOfChildren).fill(100 / numberOfChildren);
  const localStorageKey = `splitSizes.${id}.${direction}`;

  const [activeSizes, setActiveSizes] = useState<SplitProps["sizes"]>(() => {
    const savedSizes = storage.getItem(localStorageKey);
    return isValidSizes(savedSizes) ? savedSizes : sizes || defaultSizes;
  });

  // Update localStorage whenever `activeSizes` change.
  useUpdateEffect(() => {
    storage.setItem(localStorageKey, activeSizes);
  }, [activeSizes, localStorageKey]);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Split
      key={direction} // Force re-render when direction changes.
      className="SplitView"
      direction={direction}
      sizes={activeSizes ?? defaultSizes}
      minSize={minSize}
      onDragEnd={setActiveSizes} // Update sizes on drag end.
      gutterSize={gutterSize}
      style={{
        display: "flex",
        flexDirection: direction === "horizontal" ? "row" : "column",
        height: "100%",
        width: "100%",
      }}
    >
      {children}
    </Split>
  );
}

export default SplitView;
