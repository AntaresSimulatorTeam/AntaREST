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

import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { Button, type ButtonProps } from "@mui/material";
import type { ToOptions } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import RouterButton from "../router/RouterButton";

export type BackButtonProps =
  | {
      onClick?: ButtonProps["onClick"];
      linkOptions?: never;
    }
  | {
      onClick?: never;
      linkOptions?: ToOptions;
    };

function BackButton({ onClick, linkOptions }: BackButtonProps) {
  const { t } = useTranslation();
  const label = t("button.back");
  const sharedProps: ButtonProps = {
    color: "secondary",
    startIcon: <ArrowBackIcon />,
  };

  if (linkOptions) {
    return (
      <RouterButton {...sharedProps} {...linkOptions}>
        {label}
      </RouterButton>
    );
  }

  return (
    <Button {...sharedProps} onClick={onClick}>
      {label}
    </Button>
  );
}

export default BackButton;
