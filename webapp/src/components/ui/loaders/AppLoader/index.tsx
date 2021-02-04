import React from 'react';
import Particles from 'react-particles-js';
import particlesConf from './particles.json';
import './particles.css';

const AppLoader = () => (
  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', width: '100%' }}>
    <div style={{ height: '50%', width: '50%' }}>
      <Particles
        params={particlesConf}
      />
    </div>
  </div>
);

export default AppLoader;
