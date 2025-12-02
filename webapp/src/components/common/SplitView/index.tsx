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

import { Children, isValidElement, useState } from "react";
import Split, { type SplitProps } from "react-split";
import { useUpdateEffect } from "react-use";
import storage from "../../../services/utils/localStorage";
import "./style.css";

export interface SplitViewProps {
  splitId: string;
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
    sizes.reduce((sum, size) => sum + size, 0) === 100
  );
}

/**
 * Generates a stable key for a React child element.
 * This prevents DOM ref issues with react-split when children change conditionally.
 *
 * The key is based on:
 * 1. The child's existing key (if provided)
 * 2. The component type (function/class name or element type)
 * 3. The child's position index
 *
 * This ensures that when conditional rendering swaps children (e.g., SynthesisViewer <-> ResultMatrixViewer),
 * react-split's internal DOM refs are properly updated instead of being reused incorrectly.
 *
 * @param child
 * @param index
 */
function getChildKey(child: React.ReactNode, index: number): string {
  if (!isValidElement(child)) {
    return `split-child-${index}`;
  }

  // If the child already has a key, use it
  if (child.key) {
    return String(child.key);
  }

  // Generate a key based on the component type and index
  let typeIdentifier = `unknown-${index}`;

  if (typeof child.type === "string") {
    // DOM element like 'div', 'span'
    typeIdentifier = child.type;
  } else if (typeof child.type === "function") {
    // Function/Class component
    typeIdentifier = child.type.name || child.type.toString();
  } else if (child.type && typeof child.type === "object") {
    // Memo/ForwardRef component
    const componentType = child.type as { name?: string; displayName?: string };
    typeIdentifier = componentType.name || componentType.displayName || "component";
  }

  return `split-${typeIdentifier}-${index}`;
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
 * @param props.splitId - Identifier to uniquely store the sizes of the panes.
 * @param props.children - Child components to be rendered within the split views.
 * @param [props.direction=horizontal] - The orientation of the split view ("horizontal" or "vertical").
 * @param [props.sizes] - Initial sizes of each view in percentages. The array must sum to 100 and match the number of children.
 * @param [props.minSize=[150, 150]] - Minimum sizes of the elements, specified as pixel values.
 * @param [props.gutterSize=3] - The size of the gutter between split views.
 * @returns A React component displaying a split layout view with resizable panes.
 */
function SplitView({
  splitId,
  children,
  direction = "horizontal",
  sizes = [10, 90], // Most common split ratio: small sidebar (10%) + main content area (90%)
  minSize = [150, 150],
  gutterSize = 3,
}: SplitViewProps) {
  const numberOfChildren = Children.count(children);
  const defaultSizes = Array(numberOfChildren).fill(100 / numberOfChildren);
  const localStorageKey = `splitSizes.${splitId}.${direction}`;

  const [activeSizes, setActiveSizes] = useState<SplitProps["sizes"]>(() => {
    const savedSizes = storage.getItem(localStorageKey);
    return isValidSizes(savedSizes) ? savedSizes : sizes || defaultSizes;
  });

  // Update localStorage whenever `activeSizes` change.
  useUpdateEffect(() => {
    storage.setItem(localStorageKey, activeSizes?.map(Math.round));
  }, [activeSizes, localStorageKey]);

  // Generate a composite key based on direction and children identities
  // This ensures Split remounts when children change
  // preventing react-split's DOM refs from getting confused
  const childrenKeys = Children.map(children, (child, index) => getChildKey(child, index))?.join(
    "-",
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Split
      key={`${direction}-${childrenKeys}`} // Force re-render when direction or children identities change
      className="SplitView"
      direction={direction}
      sizes={activeSizes ?? defaultSizes}
      minSize={minSize}
      onDragEnd={setActiveSizes}
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
