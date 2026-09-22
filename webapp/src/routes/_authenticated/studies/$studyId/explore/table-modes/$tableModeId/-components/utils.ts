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

import type { Options } from "@/components/fieldEditors/SelectFE";
import {
  areaColumnsSchema,
  bindingConstraintColumnsSchema,
  linkColumnsSchema,
  renewableColumnsSchema,
  stStorageAdditionalConstraintColumnsSchema,
  stStorageColumnsSchema,
  tableModeTypeSchema,
  thermalColumnsSchema,
} from "@/services/api/tablemode/schemas";
import type { TableModeType } from "@/services/api/tablemode/types";

export const tableModeTypeOptions = tableModeTypeSchema.options.map((type) => ({
  value: type,
  label: (t) => t(`tableMode.type.${type}`),
})) satisfies Options<TableModeType>;

export function getTableColumnsForType<T extends TableModeType>(type: T) {
  switch (type) {
    case "areas":
      return areaColumnsSchema.element.options;
    case "links":
      return linkColumnsSchema.element.options;
    case "thermals":
      return thermalColumnsSchema.element.options;
    case "renewables":
      return renewableColumnsSchema.element.options;
    case "st-storages":
      return stStorageColumnsSchema.element.options;
    case "binding-constraints":
      return bindingConstraintColumnsSchema.element.options;
    case "st-storages-additional-constraints":
      return stStorageAdditionalConstraintColumnsSchema.element.options;
    default:
      return [];
  }
}
