import _ from "lodash";
import moment, { DurationInputArg2 } from "moment";
import { CellChange } from "handsontable/common";
import {
  MatrixEditDTO,
  MatrixStats,
  Operator,
  StudyOutputDownloadLevelDTO,
} from "../../../common/types";

export const formatDateFromIndex = (
  index: Array<string | number>
): Array<string> => {
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
        moment.utc(startDate).add(i, "h").format("YYYY/MM/DD HH:mm")
      );
    }
    // weekly
    if (index.length > 12) {
      const startDate = moment(_.padStart(String(sample), 2, "0"), "WW").year(
        2005
      );
      return index.map((e, i) =>
        moment.utc(startDate).add(i, "w").format("YYYY/MM/DD HH:mm")
      );
    }
    // monthly
    if (index.length > 1) {
      return index.map((e) =>
        moment(_.padStart(String(e), 2, "0"), "MM").format("MM/DD HH:mm")
      );
    }
  }
  return index.map((e) => String(e));
};

const convertLevelDate = (
  levelDate: StudyOutputDownloadLevelDTO
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
  startDate: string,
  levelDate: StudyOutputDownloadLevelDTO
): string | number => {
  const date = moment
    .utc(startDate)
    .add(indexDate, convertLevelDate(levelDate))
    .format("(ww) - ddd DD MMM HH:mm");
  return `${indexDate.toString().padStart(4, "0")} ${date}`.toUpperCase();
};

export const slice = (tab: CellChange[]): MatrixEditDTO[] => {
  return tab.map((cell) => {
    return {
      coordinates: [[cell[0] as number, (cell[1] as number) - 1]],
      operation: { operation: Operator.EQ, value: parseInt(cell[3], 10) },
    };
  });
};

export const computeStats = (
  statsType: string,
  row: Array<number>
): Array<number> => {
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
      { min: row[0], max: row[0], total: 0 }
    );
    return [statsInfo.min, statsInfo.max, statsInfo.total / row.length];
  }
  return [];
};

export default {};
