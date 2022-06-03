import _ from 'lodash';
import moment from 'moment';
import {formatDateFromIndex} from './utils';

test('Date from weekly input', () => {
  const weeks = Array(52).fill(0).map((e,i)=>1 + ((i+26) % 52));
  const startDate = moment("2005/07/04 00:00", "yyyy/MM/DD HH:mm");
  const weeksDate = Array(52).fill(0).map((e,i) => moment(startDate).add(i, 'w').format("yyyy/MM/DD HH:mm"));
  expect(formatDateFromIndex(weeks)).toStrictEqual(weeksDate);
});


test('Date from monthly input', () => {
  const months = Array(12).fill(0).map((e,i)=>1 + ((i+6) % 12))
  const monthsDate = [
    "07/01 00:00",
    "08/01 00:00",
    "09/01 00:00",
    "10/01 00:00",
    "11/01 00:00",
    "12/01 00:00",
    "01/01 00:00",
    "02/01 00:00",
    "03/01 00:00",
    "04/01 00:00",
    "05/01 00:00",
    "06/01 00:00",
  ]
  expect(formatDateFromIndex(months)).toStrictEqual(monthsDate);
});
