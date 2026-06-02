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

import { Box, Divider, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { TREE_ROOT_NAME } from "@/components/utils/constants";
import { chipSx, variantColor, variantLabel, type TreeVariant } from "./treeVariantUtils";

interface Props {
  variant: TreeVariant;
  onClick?: () => void;
}

function BreadcrumbRootChip({ variant, onClick }: Props) {
  const { t } = useTranslation();
  const interactive = Boolean(onClick);

  return (
    <Box
      component={interactive ? "button" : "span"}
      type={interactive ? "button" : undefined}
      onClick={onClick}
      sx={chipSx(variant, interactive)}
    >
      <Typography
        component="span"
        fontSize="small"
        sx={{
          fontWeight: 700,
          color: variantColor(variant),
          textTransform: "lowercase",
          letterSpacing: 0.3,
          lineHeight: 1,
        }}
      >
        {variantLabel(variant, t)}
      </Typography>
      <Divider orientation="vertical" sx={{ height: 11, alignSelf: "center", opacity: 0.7 }} />
      <Typography variant="caption" sx={{ lineHeight: 1.6, fontWeight: 500 }}>
        {TREE_ROOT_NAME}
      </Typography>
    </Box>
  );
}

export default BreadcrumbRootChip;
