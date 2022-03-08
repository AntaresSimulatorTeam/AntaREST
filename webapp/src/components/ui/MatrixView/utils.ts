import _ from 'lodash';
import moment from 'moment';

export const createDatesFromIndex = (index: Array<string|number>): Array<string> => {
  if (index.length === 0) {
    return [];
  }
  const sample = index[0];
  const datetimeMatch = String(sample).match(RegExp('\\d{2}/\\d{2} \\d{2}:\\d{2}'));
  if (!datetimeMatch) {
    // daily
    const dateMatch = String(sample).match(RegExp('(\\d{2})/(\\d{2})'));
    if (dateMatch) {
      return index.map((e) => moment(e, 'MM/DD').format('MM/DD HH:mm'));
    }
    // daily without information
    // TODO this should depends on the study general settings (calendar)
    // this case is when no such information is available
    console.log('here');
    if (index.length > 100) {
      const startDate = moment('01/01/2000 00:00:00', 'DD/MM/YYYY hh:mm:ss');
      console.log(startDate);
      console.log(index.map((e, i) => moment(startDate).add(i, 'h').format('YYYY/MM/DD HH:mm')));
      return index.map((e, i) => moment(startDate).add(i, 'h').format('YYYY/MM/DD HH:mm'));
    }
    // weekly
    if (index.length > 12) {
      const startDate = moment(_.padStart(String(sample), 2, '0'), 'WW').year(2005);
      return index
        .map((e, i) => moment(startDate).add(i, 'w').format('YYYY/MM/DD HH:mm'));
    }
    // monthly
    if (index.length > 1) {
      return index.map((e) => moment(_.padStart(String(e), 2, '0'), 'MM').format('MM/DD HH:mm'));
    }
  }
  return index.map((e) => String(e));
};

export default {};
