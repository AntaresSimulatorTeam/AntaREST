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

import type { TimeFrequencyType } from "../../shared/types";
import type { FilterType, TimeIndexingType } from "./constants";

export interface RowFilter {
  id: string;
  indexingType: TimeIndexingType;
  type: FilterType;
  range?: { min: number; max: number };
  list?: number[];
}

export interface FilterState {
  active: boolean;
  columnsFilter: {
    type: FilterType;
    range?: { min: number; max: number };
    list?: number[];
  };
  rowsFilters: RowFilter[];
  operation: {
    type: string;
    value: number;
  };
}

export interface FilterCriteria {
  columnsIndices: number[];
  rowsIndices: number[];
}

export interface MatrixFilterProps {
  dateTime?: string[];
  isTimeSeries: boolean;
  timeFrequency?: TimeFrequencyType;
}

export interface FilterSectionProps {
  filter: FilterState;
  setFilter: React.Dispatch<React.SetStateAction<FilterState>>;
}

export interface ColumnFilterProps extends FilterSectionProps {
  columnCount: number;
}

export interface RowFilterProps extends FilterSectionProps {
  dateTime?: string[];
  isTimeSeries: boolean;
  timeFrequency?: TimeFrequencyType;
  onAddFilter?: () => void;
  onRemoveFilter?: (id: string) => void;
  filter: FilterState;
  filterId?: string;
  expanded?: boolean;
  onToggleExpanded?: (id: string) => void;
}

export interface OperationsProps extends FilterSectionProps {
  onApplyOperation: () => void;
}

export interface SelectionSummaryProps {
  filteredData: FilterCriteria;
  previewMode?: boolean;
}

export interface TemporalIndexingParams {
  filter: FilterState;
  rowFilter: RowFilter;
  dateTime?: string[];
  isTimeSeries: boolean;
  timeFrequency?: TimeFrequencyType;
  totalRows: number;
}

export interface TemporalOption {
  value: TimeIndexingType;
  label: string;
  description: string;
}
