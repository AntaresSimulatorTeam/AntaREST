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

import { Button, type ButtonProps } from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { useTranslation } from "react-i18next";

export interface BackButtonProps {
  onClick: ButtonProps["onClick"];
}

/**
 * Back button used to navigate back to the previous page.
 * The parent element must be in "relative" position.
 *
 * @param props - The button props.
 * @returns The back button.
 */
function BackButton(props: BackButtonProps) {
  const { t } = useTranslation();

  return (
    <Button
      color="secondary"
      startIcon={<ArrowBackIcon />}
      sx={{
        position: "sticky",
        top: 0,
        left: 0,
        backdropFilter: "blur(100px)",
        zIndex: 99,
      }}
      {...props}
    >
      {t("button.back")}
    </Button>
  );
}

export default BackButton;
