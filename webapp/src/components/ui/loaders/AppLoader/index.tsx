import React from 'react';
import { useTheme } from '@material-ui/core';
import Particles from 'react-particles-js';
import particlesConf from './particles.json';
import './particles.css';

const AppLoader = () => {
  const theme = useTheme();
  return (
    <div style={{ height: '100vh', backgroundColor: theme.palette.primary.dark }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', width: '100%' }}>
        <div style={{ height: '50%', width: '50%' }}>
          <Particles
            params={particlesConf}
          />
        </div>
      </div>
    </div>
  );
};

export default AppLoader;
