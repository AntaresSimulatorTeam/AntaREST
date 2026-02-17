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

interface NavigationBreadcrumbsProps {
  items: BreadcrumbItem[];
  studyCount: number;
  onNavigate: (item: BreadcrumbItem) => void;
  activeTree: "managed" | "external";
}

function NavigationBreadcrumbs({ items, studyCount, onNavigate }: NavigationBreadcrumbsProps) {
  const { t } = useTranslation();

  return (
    <>
      <Breadcrumbs maxItems={3}>
        {items.map((item, index) => {
          const isLast = index === items.length - 1;

          return (
            <Link
              key={item.id}
              underline="hover"
              color="inherit"
              onClick={() => !isLast && onNavigate(item)}
              sx={{
                display: "flex",
                alignItems: "center",
                cursor: isLast ? "default" : "pointer",
                fontWeight: isLast ? 600 : 400,
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
