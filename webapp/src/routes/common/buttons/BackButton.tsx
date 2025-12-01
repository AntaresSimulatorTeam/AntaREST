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

import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { Button, type ButtonProps } from "@mui/material";
import { useTranslation } from "react-i18next";

export interface BackButtonProps {
  onClick: ButtonProps["onClick"];
}

function BackButton(props: BackButtonProps) {
  const { t } = useTranslation();

  return (
    <Button color="secondary" startIcon={<ArrowBackIcon />} {...props}>
      {t("button.back")}
    </Button>
  );
}

export default BackButton;
