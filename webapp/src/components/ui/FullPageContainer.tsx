import React, { PropsWithChildren } from 'react';

export default (props: PropsWithChildren<{}>) => {
  const { children } = props;
  return (
    <div style={{ overflow: 'auto', height: '100%', width: '100%' }}>
      {children}
    </div>
  );
};
