import { Theme } from '@material-ui/core';
import React, { CSSProperties } from 'react';
import { CustomNodeElementProps } from 'react-d3-tree/lib/types/common';

interface PropsType {
    rd3tProps: CustomNodeElementProps;
    theme: Theme;
    history: any;

}

const style = {
  root: (theme: Theme): CSSProperties => ({
    border: `1px solid ${theme.palette.primary.main}`,
    borderRadius: theme.shape.borderRadius,
    backgroundColor: 'white',
    width: '250px',
    height: '150px',
    boxSizing: 'border-box',
  }),
};
const VariantCard = (props: PropsType) => {
  const { rd3tProps, theme, history } = props;
  const { nodeDatum, toggleNode } = rd3tProps;
  return (
    <g>
      <foreignObject width={250} height={150} x={-125} y={-75}>
        <div onClick={() => history.push(`/study/${nodeDatum.attributes?.id}/variants`)} style={style.root(theme)}>
          <h3 style={{ textAlign: 'center', fontSize: '0.8em' }}>{nodeDatum.name}</h3>
          <h3 style={{ textAlign: 'center' }}>{nodeDatum.attributes?.id}</h3>
        </div>
      </foreignObject>
    </g>
  );
};

export default VariantCard;
