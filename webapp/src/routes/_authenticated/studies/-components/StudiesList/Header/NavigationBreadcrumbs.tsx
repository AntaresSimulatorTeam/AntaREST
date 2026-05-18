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

import { Breadcrumbs, Link, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import type { BreadcrumbItem } from "./types";
import { buildKey } from "@/utils/reactUtils";
import BreadcrumbRootChip from "../../breadcrumb/BreadcrumbRootChip";
import { separatorSx, variantColor, type TreeVariant } from "../../breadcrumb/treeVariant";

interface NavigationBreadcrumbsProps {
  items: BreadcrumbItem[];
  studyCount: number;
  activeTree: TreeVariant;
  onNavigate: (item: BreadcrumbItem) => void;
}

function NavigationBreadcrumbs({
  items,
  studyCount,
  activeTree,
  onNavigate,
}: NavigationBreadcrumbsProps) {
  const { t } = useTranslation();
  const [rootItem, ...trailingItems] = items;
  const isRootActive = items.length === 1;

  return (
    <>
      <Breadcrumbs maxItems={3} sx={separatorSx(activeTree)}>
        <BreadcrumbRootChip
          key={buildKey("__root__", 0)}
          variant={activeTree}
          onClick={isRootActive ? undefined : () => onNavigate(rootItem)}
        />

        {trailingItems.map((item, index) => {
          const isLast = index === trailingItems.length - 1;

          return (
            <Link
              key={buildKey(item.label, index + 1)}
              underline="hover"
              color={isLast ? "text.primary" : variantColor(activeTree)}
              onClick={() => !isLast && onNavigate(item)}
              sx={{
                display: "flex",
                alignItems: "center",
                cursor: isLast ? "default" : "pointer",
                fontWeight: isLast ? 600 : 500,
                transition: "color 200ms ease",
              }}
            >
              {item.label}
            </Link>
          );
        })}
      </Breadcrumbs>
      <Typography fontSize="small">
        ({studyCount} {t("global.studies").toLowerCase()})
      </Typography>
    </>
  );
}

export default NavigationBreadcrumbs;
