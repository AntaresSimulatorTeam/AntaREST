import React from 'react';
import { IOptions, RecursivePartial } from 'tsparticles';
import Particles from 'react-tsparticles';
import { useTheme } from '@material-ui/core';
import particleOptions from './particles';

const AppLoader = () => {
  const theme = useTheme();
  return (
    <div style={{ height: '100vh', backgroundColor: theme.palette.primary.dark }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', width: '100%' }}>
        <div style={{ height: '50%', width: '50%' }}>
          <Particles
            id="tsparticles"
            options={particleOptions as RecursivePartial<IOptions>}
          />
        </div>
      </div>
    </div>
  );
};

export default AppLoader;
