import React from 'react';
import Particles from 'react-tsparticles';
import { IOptions, RecursivePartial } from 'tsparticles';
import particleOptions from './particle';

function Smoke() {
  return (
    <Particles
      id="tsparticles"
      options={particleOptions as RecursivePartial<IOptions>}
    />
  );
}

export default Smoke;
