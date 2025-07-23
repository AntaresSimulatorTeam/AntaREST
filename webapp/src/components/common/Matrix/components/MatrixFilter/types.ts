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

import type { DateTimes, TimeFrequencyType } from "../../shared/types";
import type { FILTER_OPERATORS, FILTER_TYPES, TIME_INDEXING } from "./constants";

export type FilterType = (typeof FILTER_TYPES)[keyof typeof FILTER_TYPES];
export type FilterOperatorType = (typeof FILTER_OPERATORS)[keyof typeof FILTER_OPERATORS];
export type TimeIndexingType = (typeof TIME_INDEXING)[keyof typeof TIME_INDEXING];

export interface RowFilter {
  id: string;
  indexingType: TimeIndexingType;
  type: FilterType;
  range?: { min: number; max: number };
  list?: number[];
  operator?: FilterOperatorType;
}

export interface FilterState {
  active: boolean;
  columnsFilter: {
    type: FilterType;
    range?: { min: number; max: number };
    list?: number[];
    operator?: FilterOperatorType;
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
  dateTime?: DateTimes;
  isTimeSeries: boolean;
  timeFrequency?: TimeFrequencyType;
  readOnly?: boolean;
}

export interface FilterSectionProps {
  filter: FilterState;
  setFilter: React.Dispatch<React.SetStateAction<FilterState>>;
}

export interface ColumnFilterProps extends FilterSectionProps {
  columnCount: number;
}

export interface DateInfo {
  dayOfYear: number;
  hourOfYear: number;
  dayOfMonth: number;
  week: number;
  month: number; // 1-12
  dayHour: number; // 0-23
  weekday: number; // Monday is 1, Sunday 7
}

export interface RowFilterProps extends FilterSectionProps {
  datesInfo?: DateInfo[];
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
}

export interface TemporalIndexingParams {
  filter: FilterState;
  rowFilter: RowFilter;
  datesInfo?: DateInfo[];
  isTimeSeries: boolean;
  timeFrequency?: TimeFrequencyType;
  totalRows: number;
}

export interface TemporalOption {
  value: TimeIndexingType;
  label: string;
}

export interface IndexedValue {
  index: number;
  value: number;
}

export interface SliderMark {
  value: number;
  label: string;
}

export interface TemporalRange {
  min: number;
  max: number;
}

export interface LocalizedTimeLabel {
  value: number;
  label: string;
  shortLabel: string;
}
