import { Theme } from '@material-ui/core';
import React from 'react';
import { CustomNodeElementProps } from 'react-d3-tree/lib/types/common';

interface PropsType {
    rd3tProps: CustomNodeElementProps;
    theme: Theme;
}

const VariantCard = (props: PropsType) => {
  const { rd3tProps, theme } = props;
  const { nodeDatum, toggleNode } = rd3tProps;
  return (
    <g>
      <circle r={0} />
      {/* `foreignObject` requires width & height to be explicitly set. */}
      <foreignObject width={250} height={150} x={-125} y={-75}>
        <div onClick={() => alert(nodeDatum.attributes?.title)} style={{ border: `1px solid ${theme.palette.primary.main}`, borderRadius: theme.shape.borderRadius, backgroundColor: 'white', width: '250px', height: '150px', boxSizing: 'border-box' }}>
          <h3 style={{ textAlign: 'center' }}>{nodeDatum.name}</h3>
          <h3 style={{ textAlign: 'center' }}>{nodeDatum.attributes?.title}</h3>
        </div>
      </foreignObject>
    </g>
  );
};

export default VariantCard;
