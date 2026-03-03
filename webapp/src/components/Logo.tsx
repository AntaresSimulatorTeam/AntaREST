/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
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

import logo from "@/assets/img/logo.png";
import { Box, keyframes, styled } from "@mui/material";

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

export const BorderedPulsating = styled(Box)(({ theme }) => [
  {
    "&::before": {
      content: '""',
      position: "absolute",
      height: "inherit",
      width: "inherit",
      border: `1px solid ${theme.palette.primary.main}`,
      borderRadius: "50%",
      animation: `${pulsatingAnimation} 2s infinite`,
      boxShadow: `0 0px 10px 0 ${theme.palette.primary.main}`,
    },
  },
  theme.applyStyles("dark", {
    border: `1px solid ${theme.palette.secondary.main}`,
    boxShadow: `0 0px 10px 0 ${theme.palette.secondary.main}`,
  }),
]);

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
