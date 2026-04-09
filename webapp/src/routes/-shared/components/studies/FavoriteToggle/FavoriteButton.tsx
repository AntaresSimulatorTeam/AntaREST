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

import StarIcon from "@mui/icons-material/Star";
import StarBorderIcon from "@mui/icons-material/StarBorder";
import {
  IconButton,
  Tooltip,
  type IconButtonProps,
  type SvgIconOwnProps,
  type SxProps,
  type Theme,
  type TooltipProps,
} from "@mui/material";
import { useTranslation } from "react-i18next";

export interface FavoriteButtonProps {
  isFavorite: boolean;
  onClick: NonNullable<IconButtonProps["onClick"]>;
  edge?: IconButtonProps["edge"];
  tooltipPlacement?: TooltipProps["placement"];
  loading?: boolean;
  slotProps?: {
    icon?: SvgIconOwnProps;
  };
  sx?: SxProps<Theme>;
}

function FavoriteButton({
  isFavorite,
  tooltipPlacement,
  onClick,
  slotProps,
  ...rest
}: FavoriteButtonProps) {
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    event.stopPropagation();
    onClick(event);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Tooltip
      title={isFavorite ? t("studies.removeFavorite") : t("studies.addFavorite")}
      placement={tooltipPlacement}
    >
      <IconButton color="primary" size="small" onClick={handleClick} {...rest}>
        {isFavorite ? <StarIcon {...slotProps?.icon} /> : <StarBorderIcon {...slotProps?.icon} />}
      </IconButton>
    </Tooltip>
  );
}

export default FavoriteButton;
