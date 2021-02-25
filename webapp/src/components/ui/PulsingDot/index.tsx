import React from 'react';
import './style.css';

interface PropTypes {
  style: React.CSSProperties;
}

export default (props: PropTypes) => {
  const { style = {} } = props;
  return <div className="pulse yellow" style={style} />;
};
