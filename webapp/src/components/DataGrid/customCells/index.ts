/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
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

export { default as selectCellRenderer } from "./SelectCell";
export type { SelectCell, SelectCellProps } from "./SelectCell";

export { default as toggleCellRenderer } from "./ToggleCell";
export type { ToggleCell, ToggleCellProps } from "./ToggleCell";

export { default as buttonCellRenderer } from "./ButtonCell";
export type { ButtonCell, ButtonCellProps, ButtonVariant } from "./ButtonCell";

import selectCellRenderer from "./SelectCell";
import toggleCellRenderer from "./ToggleCell";
import buttonCellRenderer from "./ButtonCell";

/**
 * All custom renderers collected in a single array.
 * Pass this directly to `<DataEditor customRenderers={ALL_CUSTOM_RENDERERS} />`.
 *
 * @example
 * <DataGrid customRenderers={ALL_CUSTOM_RENDERERS} ... />
 */
export const ALL_CUSTOM_RENDERERS = [
  selectCellRenderer,
  toggleCellRenderer,
  buttonCellRenderer,
] as const;
