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
import type { TimeFrequencyType } from "../../../shared/types";
import { TIME_INDEXING } from "../constants";
import { getDefaultRangeForIndexType } from "../utils/dateUtils";
import type { DateInfo } from "@/components/common/Matrix/components/MatrixFilter/types";
import { INDEX_TYPE_TO_DATEINFO_PROPERTY } from "@/components/common/Matrix/components/MatrixFilter/utils";
interface UseTemporalDataProps {
  datesInfo?: DateInfo[];
  isTimeSeries: boolean;
  timeFrequency?: TimeFrequencyType;
}

export function useTemporalData({ datesInfo }: UseTemporalDataProps) {
  const indexTypeRanges = useMemo(() => {
    return Object.values(TIME_INDEXING).reduce(
      (acc, type) => {
        acc[type] = getDefaultRangeForIndexType(type);
        return acc;
      },
      {} as Record<string, { min: number; max: number }>,
    );
  }, []);

  const temporalValues = useMemo(() => {
    if (!datesInfo || datesInfo.length === 0) {
      return {};
    }

    const result: Record<string, number[]> = {};

    for (const indexType of Object.values(TIME_INDEXING)) {
      const property = INDEX_TYPE_TO_DATEINFO_PROPERTY[indexType];
      result[indexType] = datesInfo.map((parsed) => parsed[property] as number);
    }

    return result;
  }, [datesInfo]);

  const valuesByIndexType = useMemo(() => {
    // Start with a fresh object using the default ranges
    const result = { ...indexTypeRanges } as Record<
      string,
      { min: number; max: number; uniqueValues?: number[] }
    >;

    // Set static values that don't depend on data
    result[TIME_INDEXING.DAY_HOUR] = {
      min: 0,
      max: 23,
      uniqueValues: Array.from({ length: 24 }, (_, i) => i),
    };

    result[TIME_INDEXING.WEEKDAY] = {
      min: 1,
      max: 7,
      uniqueValues: Array.from({ length: 7 }, (_, i) => i + 1),
    };

    result[TIME_INDEXING.MONTH] = {
      min: 1,
      max: 12,
      uniqueValues: Array.from({ length: 12 }, (_, i) => i + 1),
    };

    // Only try to extract data-based values if we have parsed dates
    if (datesInfo && datesInfo.length > 0) {
      // Only update the ranges that should be data-dependent
      const dynamicTypes = [
        TIME_INDEXING.DAY_OF_YEAR,
        TIME_INDEXING.HOUR_YEAR,
        TIME_INDEXING.DAY_OF_MONTH,
        TIME_INDEXING.WEEK,
      ];

      for (const indexType of dynamicTypes) {
        const values = temporalValues[indexType];
        if (values.length > 0) {
          const uniqueSet = new Set(values);
          const uniqueValues = Array.from(uniqueSet).sort((a, b) => a - b);
          result[indexType] = {
            min: Math.min(...uniqueValues),
            max: Math.max(...uniqueValues),
            uniqueValues,
          };
        }
      }
    }

    return result;
  }, [datesInfo, indexTypeRanges, temporalValues]);

  return {
    indexTypeRanges,
    valuesByIndexType,
    temporalValues,
  };
}
