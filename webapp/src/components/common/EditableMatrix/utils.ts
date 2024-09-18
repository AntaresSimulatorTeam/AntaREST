/** Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import _ from "lodash";
import moment, { DurationInputArg2 } from "moment";
import HT from "handsontable";
import {
  MatrixEditDTO,
  MatrixIndex,
  MatrixStats,
  Operator,
  StudyOutputDownloadLevelDTO,
} from "../../../common/types";

export const formatDateFromIndex = (
  index: Array<string | number>,
): string[] => {
  if (index.length === 0) {
    return [];
  }
  const sample = index[0];
  const datetimeMatch = String(sample).match(/\d{2}\/\d{2} \d{2}:\d{2}/);
  if (!datetimeMatch) {
    // daily
    const dateMatch = String(sample).match(/(\d{2})\/(\d{2})/);
    if (dateMatch) {
      return index.map((e) => moment(e, "MM/DD").format("MM/DD HH:mm"));
    }
    // daily without information
    // TODO this should depends on the study general settings (calendar)
    // this case is when no such information is available
    if (index.length > 100) {
      const startDate = moment("01/01/2000 00:00:00", "DD/MM/YYYY hh:mm:ss");
      return index.map((e, i) =>
        moment.utc(startDate).add(i, "h").format("YYYY/MM/DD HH:mm"),
      );
    }
    // weekly
    if (index.length > 12) {
      const startDate = moment(2005, "YYYY").week(sample as number);
      return index.map((e, i) =>
        moment.utc(startDate).add(i, "w").format("YYYY/MM/DD HH:mm"),
      );
    }
    // monthly
    if (index.length > 1) {
      return index.map((e) =>
        moment(_.padStart(String(e), 2, "0"), "MM").format("MM/DD HH:mm"),
      );
    }
  }
  return index.map((e) => String(e));
};

const convertLevelDate = (
  levelDate: StudyOutputDownloadLevelDTO,
): DurationInputArg2 => {
  if (levelDate === StudyOutputDownloadLevelDTO.ANNUAL) {
    return "year";
  }
  if (levelDate === StudyOutputDownloadLevelDTO.DAILY) {
    return "day";
  }
  if (levelDate === StudyOutputDownloadLevelDTO.HOURLY) {
    return "hour";
  }
  if (levelDate === StudyOutputDownloadLevelDTO.MONTHLY) {
    return "month";
  }
  return "week";
};

export const createDateFromIndex = (
  indexDate: string | number,
  matrixIndex: MatrixIndex,
): string | number => {
  const date = moment
    .utc(matrixIndex.start_date)
    .add(indexDate, convertLevelDate(matrixIndex.level))
    .format(
      matrixIndex.level === StudyOutputDownloadLevelDTO.HOURLY
        ? "ddd DD MMM HH:mm"
        : "ddd DD MMM",
    );
  return date;
};

export const cellChangesToMatrixEdits = (
  cellChanges: HT.CellChange[],
  matrixTime: boolean,
  isPercentEnabled: boolean,
): MatrixEditDTO[] =>
  cellChanges.map(([row, column, , value]) => {
    const rowIndex = parseFloat(row.toString());
    const colIndex = parseFloat(column.toString()) - (matrixTime ? 1 : 0);

    return {
      coordinates: [[rowIndex, colIndex]],
      operation: {
        operation: Operator.EQ,
        value: isPercentEnabled ? parseFloat(value) / 100 : parseFloat(value),
      },
    };
  });

export const computeStats = (statsType: string, row: number[]): number[] => {
  if (statsType === MatrixStats.TOTAL) {
    return [
      row.reduce((agg, value) => {
        return agg + value;
      }, 0),
    ];
  }
  if (statsType === MatrixStats.STATS) {
    const statsInfo = row.reduce(
      (agg, value) => {
        const newAgg = { ...agg };
        if (value < agg.min) {
          newAgg.min = value;
        }
        if (value > agg.max) {
          newAgg.max = value;
        }
        newAgg.total = agg.total + value;

        return newAgg;
      },
      { min: row[0], max: row[0], total: 0 },
    );
    return [statsInfo.min, statsInfo.max, statsInfo.total / row.length];
  }
  return [];
};

export default {};
