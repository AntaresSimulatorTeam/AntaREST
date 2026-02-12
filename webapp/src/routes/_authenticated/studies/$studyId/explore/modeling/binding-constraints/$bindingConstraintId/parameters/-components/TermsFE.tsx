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

import CustomScrollbar from "@/components/CustomScrollbar";
import NumberFE from "@/components/fieldEditors/NumberFE";
import type {
  BindingConstraint,
  BindingConstraintClusterTermData,
  BindingConstraintLinkTermData,
} from "@/services/api/studies/bindingConstraints/type";
import AddCircleOutlineRoundedIcon from "@mui/icons-material/AddCircleOutlineRounded";
import LinkIcon from "@mui/icons-material/Link";
import LocalFireDepartmentIcon from "@mui/icons-material/LocalFireDepartment";
import RemoveCircleIcon from "@mui/icons-material/RemoveCircle";
import RemoveCircleOutlineIcon from "@mui/icons-material/RemoveCircleOutline";

import SelectFE, { type Options } from "@/components/fieldEditors/SelectFE";
import {
  getBindingConstraintTermType,
  type BindingConstraintTermType,
} from "@/services/api/studies/bindingConstraints/utils";
import AddCircleIcon from "@mui/icons-material/AddCircle";
import {
  Button,
  Divider,
  FormHelperText,
  IconButton,
  InputAdornment,
  List,
  ListItem,
  ListItemIcon,
  ListSubheader,
  Paper,
  Skeleton,
  Stack,
  Typography,
} from "@mui/material";
import { Fragment, useRef } from "react";
import { useController, useFieldArray, useFormContext } from "react-hook-form";
import { useTranslation } from "react-i18next";
import ClusterTermDataFE from "./ClusterTermDataFE";
import LinkTermDataFE from "./LinkTermDataFE";

const DATA_BY_TERM_TYPE = {
  link: {
    icon: LinkIcon,
    editor: LinkTermDataFE,
    defaultData: { area1: "", area2: "" } satisfies BindingConstraintLinkTermData,
  },
  cluster: {
    icon: LocalFireDepartmentIcon,
    editor: ClusterTermDataFE,
    defaultData: { area: "", cluster: "" } satisfies BindingConstraintClusterTermData,
  },
} as const;

const TYPE_OPTIONS = [
  { value: "link", icon: DATA_BY_TERM_TYPE.link.icon, label: (t) => t("study.link") },
  { value: "cluster", icon: DATA_BY_TERM_TYPE.cluster.icon, label: (t) => t("study.cluster") },
] as const satisfies Options<BindingConstraintTermType>;

function TermsFE() {
  const { t } = useTranslation();
  const { control } = useFormContext<BindingConstraint>();
  const newTermTypeRef = useRef<BindingConstraintTermType>();

  const { fields, append, update, remove } = useFieldArray({
    control,
    name: "terms",
  });

  const {
    formState: { isLoading, isSubmitting, disabled },
    fieldState: { invalid, error },
  } = useController({
    name: "terms",
    control,
  });

  const isDisabled = isSubmitting || disabled;
  const textColor = isDisabled ? "textDisabled" : "textSecondary";

  ////////////////////////////////////////////////////////////////
  // Validation
  ////////////////////////////////////////////////////////////////

  const handleOffsetValidate = (value?: number) => {
    if (typeof value !== "number" || value === 0) {
      return t("form.field.invalidValue");
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Paper
      elevation={2}
      sx={[
        {
          mr: 1, // For scrollbar space with the parent scrollbar
          display: "flex",
          flexDirection: "column",
          overflow: "auto",
          minHeight: 345,
        },
        invalid && { borderColor: "error.main", borderWidth: 0.5, borderStyle: "solid" },
      ]}
    >
      <ListSubheader disableSticky>{t("study.modeling.bindingConst.terms")}</ListSubheader>
      <List disablePadding sx={{ overflow: "auto" }}>
        {isLoading &&
          Array.from({ length: 3 }).map((_, index) => (
            <ListItem disablePadding key={index}>
              <Skeleton sx={{ width: 1, height: 60, mx: 2 }} />
            </ListItem>
          ))}
        {fields.map((term, index) => {
          const termType = getBindingConstraintTermType(term);

          if (!termType) {
            return null;
          }

          const { icon: TermIcon, editor: TermDataFE } = DATA_BY_TERM_TYPE[termType];

          return (
            <Fragment key={term.id}>
              <ListItem
                secondaryAction={
                  <IconButton edge="end" disabled={isDisabled} onClick={() => remove(index)}>
                    <RemoveCircleIcon />
                  </IconButton>
                }
              >
                <ListItemIcon sx={{ minWidth: 40 }}>
                  <TermIcon color={isDisabled ? "disabled" : "inherit"} />
                </ListItemIcon>
                <CustomScrollbar>
                  <Stack spacing={1} sx={{ width: "min-content", py: 1 }}>
                    <NumberFE
                      label={t("study.modeling.bindingConst.weight")}
                      control={control}
                      name={`terms.${index}.weight`}
                      size="extra-small"
                      sx={{ minWidth: 80 }}
                    />
                    <Typography color={textColor}>×</Typography>
                    <TermDataFE index={index} />
                    {typeof term.offset === "number" ? (
                      <>
                        <Typography noWrap sx={{ letterSpacing: 4, width: 1 }} color={textColor}>
                          × t +
                        </Typography>
                        <NumberFE
                          label={t("study.modeling.bindingConst.offset")}
                          control={control}
                          rules={{ validate: handleOffsetValidate }}
                          name={`terms.${index}.offset`}
                          size="extra-small"
                          sx={{
                            minWidth: 110,
                            mr: 1, // To prevent parent to always display scrollbar
                          }}
                          slotProps={{
                            input: {
                              endAdornment: (
                                <InputAdornment position="end">
                                  <IconButton
                                    edge="end"
                                    onClick={() => {
                                      const { offset, ...newTerm } = term;
                                      update(index, newTerm);
                                    }}
                                    disabled={isDisabled}
                                  >
                                    <RemoveCircleOutlineIcon />
                                  </IconButton>
                                </InputAdornment>
                              ),
                            },
                          }}
                        />
                      </>
                    ) : (
                      <Button
                        variant="outlined"
                        color="secondary"
                        startIcon={<AddCircleOutlineRoundedIcon />}
                        onClick={() => update(index, { ...term, offset: 0 })}
                        disabled={isDisabled}
                      >
                        {t("study.modeling.bindingConst.offset")}
                      </Button>
                    )}
                  </Stack>
                </CustomScrollbar>
              </ListItem>
              {index < fields.length - 1 && (
                <Divider variant="inset" textAlign="left" component="li">
                  <Typography color={textColor}>+</Typography>
                </Divider>
              )}
            </Fragment>
          );
        })}
      </List>
      <Divider />
      <Stack spacing={1} justifyContent="center" sx={{ width: 1, pb: 1, pt: 1.5 }}>
        <Button
          onClick={() => {
            if (newTermTypeRef.current) {
              append({
                weight: 0,
                data: DATA_BY_TERM_TYPE[newTermTypeRef.current].defaultData,
              });
            }
          }}
          startIcon={<AddCircleIcon />}
          color="inherit"
          disabled={isDisabled}
        >
          {t("global.add")}
        </Button>
        <SelectFE
          label="Term type"
          defaultValue={TYPE_OPTIONS[0].value}
          options={TYPE_OPTIONS}
          startCaseLabel
          size="extra-small"
          sx={{ minWidth: 100 }}
          inputRef={(ref) => (newTermTypeRef.current = ref?.value)}
          disabled={isDisabled}
        />
      </Stack>
      {invalid && (
        <FormHelperText error sx={{ mx: 2, my: 1 }}>
          {error?.message}
        </FormHelperText>
      )}
    </Paper>
  );
}

export default TermsFE;
