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

import { OverlayScrollbarsComponent } from "overlayscrollbars-react";
import type { EventListeners, PartialOptions } from "overlayscrollbars";
import useThemeColorScheme from "@/hooks/useThemeColorScheme";
import "overlayscrollbars/overlayscrollbars.css";
import "./styles.css";

export interface CustomScrollbarProps<T extends React.ElementType = "div"> {
  element?: T;
  options?: PartialOptions;
  events?: EventListeners;
  defer?: boolean | IdleRequestOptions;
  children?: React.ReactNode;
}

function CustomScrollbar<T extends React.ElementType>({
  options,
  ...rest
}: CustomScrollbarProps<T>) {
  const { isDarkMode } = useThemeColorScheme();

  return (
    <OverlayScrollbarsComponent
      element="div"
      options={{
        ...options,
        scrollbars: {
          theme: isDarkMode ? "os-theme-dark" : "os-theme-light",
          autoHide: "never",
          autoHideDelay: 250,
          ...options?.scrollbars,
        },
      }}
      defer
      {...rest}
    />
  );
}

export default CustomScrollbar;
