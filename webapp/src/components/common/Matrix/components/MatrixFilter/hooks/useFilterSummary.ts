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

import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import type { FilterState } from "../types";

interface FilterSummary {
  columnFilterText: string;
  rowFilterTexts: string[];
}

export function useFilterSummary(filter: FilterState): FilterSummary {
  const { t } = useTranslation();

  return useMemo(() => {
    if (!filter.active) {
      return { columnFilterText: "", rowFilterTexts: [] };
    }

    const { columnsFilter, rowsFilters } = filter;
    let columnFilterText = "";
    const rowFilterTexts: string[] = [];

    // Column filter summary
    if (columnsFilter.type === "range" && columnsFilter.range) {
      columnFilterText = `${t("matrix.filter.columns")}: ${columnsFilter.range.min} - ${columnsFilter.range.max}`;
    } else if (columnsFilter.type === "list" && columnsFilter.list) {
      columnFilterText = `${t("matrix.filter.columns")}: [${columnsFilter.list.join(", ")}]`;
    }

    // Row filters summary (multiple)
    for (const rowFilter of rowsFilters) {
      const indexType = t(`matrix.filter.indexing.${rowFilter.indexingType}`);

      if (rowFilter.type === "range" && rowFilter.range) {
        rowFilterTexts.push(
          `${t("matrix.filter.rows")} (${indexType}): ${rowFilter.range.min} - ${rowFilter.range.max}`,
        );
      } else if (rowFilter.type === "list" && rowFilter.list) {
        rowFilterTexts.push(
          `${t("matrix.filter.rows")} (${indexType}): [${rowFilter.list.join(", ")}]`,
        );
      }
    }

    return { columnFilterText, rowFilterTexts };
  }, [filter, t]);
}
