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

import "jsoneditor";

declare module "jsoneditor" {
  export interface HistoryItem {
    action: string;
    params: object;
    timestamp: Date;
  }

  export default interface JSONEditor {
    /**
     * Only available for mode `code`.
     */
    aceEditor?: AceAjax.Editor;
    /**
     * Expand all fields. Only applicable for mode `tree`, `view`, and `form`.
     */
    expandAll?: VoidFunction;
    /**
     * Only available for mode `tree`, `form`, and `preview`.
     */
    history?: {
      /**
       * Only available for mode `tree`, and `form`.
       */
      history?: HistoryItem[];
      index: number;
      onChange: () => void;
    };
    menu: HTMLDivElement;
  }
}
