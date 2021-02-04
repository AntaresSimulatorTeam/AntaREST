import React from 'react';
import ReactJson from 'react-json-view';

interface PropTypes {
  data: string;
}

const StudyJsonView = (props: PropTypes) => {
  const { data } = props;
  return (
    <div>
      <ReactJson src={JSON.parse(data)} />
    </div>
  );
};

export default StudyJsonView;
