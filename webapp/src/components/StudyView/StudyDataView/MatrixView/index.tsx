import React, { useEffect, useRef } from 'react';
import jspreadsheet from 'jspreadsheet-ce';
import { MatrixType } from '../../../../common/types';
import './jexcel.css';
import './jsuites.css';

interface PropTypes {
  data: MatrixType;
}

export default function MatrixView(props: PropTypes) {
  // eslint-disable-next-line react/destructuring-assignment
  const { data = [], columns = [], index = [] } = props.data;
  const jRef = useRef(null);

  const prependIndex = index.length > 0 && typeof index[0] == 'string';
  const options = {
    data: prependIndex ? data.map((row, i) => [index[i]].concat(row)) : data,
    columns: (prependIndex ? [{ title: 'Time', width: 100, type: 'string' }] : []).concat(
      columns.map((title) => ({ title: String(title), width: 100, type: 'number' })),
    ),
  };

  useEffect(() => {
    if (jRef === null) return;

    const { current } = jRef;
    if (current === null) return;

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    if (!(current as any).jspreadsheet) {
      jspreadsheet(jRef.current, options);
    }
  }, [options]);

  return (
    <div>
      <div ref={jRef} />
    </div>
  );
}
