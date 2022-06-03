import _ from "lodash";
import moment, { DurationInputArg2 } from "moment";
// eslint-disable-next-line import/no-unresolved
import { CellChange } from "handsontable/common";
import { MatrixEditDTO, Operator } from "../../../common/types";

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

export const createDateFromIndex = (
  indexDate: string | number,
  startDate: string,
  index: (string | number)[]
): string | number => {
  let levelDate: DurationInputArg2 = "h";
  if (index.length === 8760) {
    levelDate = "h";
  } else if (index.length === 12) {
    levelDate = "m";
  } else if (index.length === 365 || index.length === 366) {
    levelDate = "d";
  } else if (index.length === 52) {
    levelDate = "w";
  }
  const date = moment
    .utc(startDate)
    .add(indexDate, levelDate)
    .format("(ww) - ddd DD MMM HH:mm");
  return `${indexDate.toString().padStart(4, "0")} ${date}`.toUpperCase();
};

export const slice = (tab: CellChange[]): MatrixEditDTO[] => {
  return tab.map((cell) => {
    return {
      slices: [
        {
          row_from: cell[0],
          row_to: cell[0] + 1,
          column_from: (cell[1] as number) - 1,
          column_to: cell[1] as number,
        },
      ],
      operation: { operation: Operator.EQ, value: parseInt(cell[3], 10) },
    };
  });
};

export default {};
