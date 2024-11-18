/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import { useEffect, useRef, useState } from "react";

/**
 * Custom hook to manage portal creation and cleanup for matrices in split views.
 * This hook is specifically designed to work around a limitation where multiple
 * Glide Data Grid instances compete for a single portal with id="portal".
 *
 * @returns Hook handlers and ref to be applied to the matrix container
 *
 * @example
 * ```tsx
 * function MatrixGrid() {
 *   const { containerRef, handleMouseEnter, handleMouseLeave } = useMatrixPortal();
 *
 *   return (
 *     <div ref={containerRef} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave}>
 *       <DataEditor ... />
 *     </div>
 *   );
 * }
 * ```
 */
export function useMatrixPortal() {
  const [isActive, setIsActive] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let portal = document.getElementById("portal");

    if (!portal) {
      portal = document.createElement("div");
      portal.id = "portal";
      portal.style.position = "fixed";
      portal.style.left = "0";
      portal.style.top = "0";
      portal.style.zIndex = "9999";
      portal.style.display = "none";
      document.body.appendChild(portal);
    }

    // Update visibility based on active state
    if (containerRef.current && isActive) {
      portal.style.display = "block";
    } else {
      portal.style.display = "none";
    }
  }, [isActive]);

  const handleMouseEnter = () => {
    setIsActive(true);
  };

  const handleMouseLeave = () => {
    setIsActive(false);
  };

  return {
    containerRef,
    handleMouseEnter,
    handleMouseLeave,
  };
}
