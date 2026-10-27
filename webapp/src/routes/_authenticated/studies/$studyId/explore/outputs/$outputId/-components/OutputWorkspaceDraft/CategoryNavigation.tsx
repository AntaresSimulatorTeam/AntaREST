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

import FolderOpenOutlinedIcon from "@mui/icons-material/FolderOpenOutlined";
import {
  Autocomplete,
  Box,
  Chip,
  Divider,
  List,
  ListItemButton,
  ListItemText,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import type { WorkspaceVariant } from ".";

export interface ResultCategory {
  id: string;
  label: string;
  example?: boolean;
}

interface Props {
  categories: ResultCategory[];
  value: ResultCategory;
  onChange: (category: ResultCategory) => void;
  variant: WorkspaceVariant;
  filesActive: boolean;
  fileCount?: number;
  navigationLabel?: string;
  onOpenFiles: VoidFunction;
}

function CategoryNavigation({
  categories,
  value,
  onChange,
  variant,
  filesActive,
  fileCount,
  navigationLabel,
  onOpenFiles,
}: Props) {
  const { t } = useTranslation();

  if (variant === "explorer" || variant === "fixed") {
    return (
      <Stack direction="column" sx={{ width: 1, minWidth: 0 }}>
        <Typography variant="overline" color="text.secondary" sx={{ px: 1, fontSize: 10 }}>
          {navigationLabel ?? t("outputDesign.resultCategories")}
        </Typography>
        <List
          dense
          disablePadding
          sx={{ maxHeight: variant === "fixed" ? "min(280px, 35vh)" : 390, overflow: "auto" }}
        >
          {categories.map((category, index) => (
            <Box key={category.id}>
              {category.example && !categories[index - 1]?.example && (
                <Typography
                  variant="caption"
                  color="text.secondary"
                  sx={{ display: "block", px: 1, pt: 1, pb: 0.5, fontSize: 10 }}
                >
                  {t("outputDesign.gemsExamples")}
                </Typography>
              )}
              <Tooltip title={category.label} placement="right">
                <ListItemButton
                  selected={!filesActive && value.id === category.id}
                  onClick={() => onChange(category)}
                  sx={{ minHeight: 29, py: 0.25, px: 1, borderRadius: 0.5 }}
                >
                  <ListItemText
                    primary={category.label}
                    slotProps={{ primary: { noWrap: true, fontSize: 12 } }}
                  />
                </ListItemButton>
              </Tooltip>
            </Box>
          ))}
        </List>
        {variant === "explorer" && (
          <>
            <Divider sx={{ my: 1 }} />
            <ListItemButton
              selected={filesActive}
              onClick={onOpenFiles}
              sx={{ gap: 1, minHeight: 36, px: 1, borderRadius: 0.5 }}
            >
              <FolderOpenOutlinedIcon sx={{ fontSize: 18 }} />
              <ListItemText
                primary={t("outputDesign.outputFiles")}
                slotProps={{ primary: { fontSize: 12 } }}
              />
              {fileCount !== undefined && (
                <Chip label={fileCount} size="small" sx={{ height: 20, fontSize: 10 }} />
              )}
            </ListItemButton>
          </>
        )}
        <Divider sx={{ mt: 1, mb: 0.5 }} />
        {!filesActive && !value.example && (
          <Typography variant="overline" color="text.secondary" sx={{ px: 1, fontSize: 10 }}>
            {value.label}
          </Typography>
        )}
      </Stack>
    );
  }

  return (
    <Stack direction="column" spacing={0.75} sx={{ width: 1, minWidth: 0, pt: 1, pb: 0.75 }}>
      <Autocomplete
        fullWidth
        disableClearable
        size="extra-small"
        options={categories}
        value={value}
        isOptionEqualToValue={(option, selected) => option.id === selected.id}
        getOptionLabel={(option) => option.label}
        groupBy={({ example }) =>
          example ? t("outputDesign.gemsExamples") : t("outputDesign.actualResults")
        }
        onChange={(_event, category) => onChange(category)}
        renderInput={(params) => (
          <TextField
            {...params}
            fullWidth
            size="extra-small"
            label={navigationLabel ?? t("outputDesign.resultCategory")}
          />
        )}
        slotProps={{
          popper: { sx: { minWidth: 320, maxWidth: "90vw" } },
          listbox: { sx: { maxHeight: 440 } },
        }}
      />
      <Typography variant="caption" color="text.secondary" sx={{ px: 0.5, fontSize: 11 }}>
        {value.example
          ? t("outputDesign.exampleTaxonomy")
          : t("outputDesign.categoryHint", { count: categories.length })}
      </Typography>
    </Stack>
  );
}

export default CategoryNavigation;
