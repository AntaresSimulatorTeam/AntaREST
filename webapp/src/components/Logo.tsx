/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import { Box, keyframes, styled } from "@mui/material";
import logo from "../../assets/img/logo.png";

const pulsatingAnimation = keyframes`
  0% {
    opacity: 1
  }
  50% {
    opacity: 0
  }
  100% {
    opacity: 1
  }
`;

export const BorderedPulsating = styled(Box)(({ theme: { palette } }) => ({
  "&::before": {
    content: '""',
    position: "absolute",
    height: "inherit",
    width: "inherit",
    border: `1px solid ${palette.mode === "dark" ? palette.secondary.main : palette.primary.main}`,
    borderRadius: "50%",
    animation: `${pulsatingAnimation} 2s infinite`,
    boxShadow: `0 0px 10px 0 ${palette.mode === "dark" ? palette.secondary.main : palette.primary.main}`,
  },
}));

export interface LogoProps {
  size?: number;
  pulse?: boolean;
}

function Logo({ size = 32, pulse = false }: LogoProps) {
  const logoEl = <img src={logo} alt="logo" style={{ height: size }} />;

  return pulse ? (
    <BorderedPulsating height={size} width={size}>
      {logoEl}
    </BorderedPulsating>
  ) : (
    logoEl
  );
}

export default Logo;
