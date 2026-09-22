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

import reactHookFormSupport, { type ReactHookFormSupportProps } from "@/hoc/reactHookFormSupport";
import {
  createFakeBlurEventHandler,
  createFakeChangeEventHandler,
  createFakeInputElement,
  type FakeBlurEventHandler,
  type FakeChangeEventHandler,
  type InputObject,
} from "@/utils/feUtils";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import RemoveCircleIcon from "@mui/icons-material/RemoveCircle";
import {
  Autocomplete,
  Box,
  Button,
  FormControl,
  FormHelperText,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Paper,
  setRef,
  Typography,
} from "@mui/material";
import * as RA from "ramda-adjunct";
import { useEffect, useState, type JSX } from "react";
import type { FieldPath, FieldValues } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { useUpdateEffect } from "react-use";
import StringFE from "../StringFE";
import { makeLabel, makeListItems } from "./utils";

interface ListFEProps<TItem, TOption> {
  defaultValue?: TItem[];
  value?: TItem[];
  options?: TOption[];
  label?: string;
  getOptionLabel?: (option: TOption) => string;
  getValueLabel?: (value: TItem) => string;
  optionToItem?: (option: TOption) => TItem;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  inputRef?: React.Ref<any>;
  name?: string;
  onChange?: (event: FakeChangeEventHandler) => void;
  onBlur?: (event: FakeBlurEventHandler) => void;
  // TODO to implement
  error?: boolean;
  helperText?: string;
}

function ListFE<TItem, TOption>(props: ListFEProps<TItem, TOption>) {
  const {
    value,
    defaultValue,
    label,
    options = [],
    getOptionLabel = makeLabel,
    getValueLabel = makeLabel,
    optionToItem = (option: TOption) => option as unknown as TItem,
    inputRef,
    name,
    onChange,
    onBlur,
    error,
    helperText,
  } = props;

  const { t } = useTranslation();
  const [listItems, setListItems] = useState(() => makeListItems(value || defaultValue || []));
  const [selectedOption, setSelectedOption] = useState<TOption | null>(null);

  // Update list if the FE is controlled (`defaultValue` is for uncontrolled)
  useUpdateEffect(() => {
    setListItems(() => makeListItems(value || []));
  }, [JSON.stringify(value)]);

  // Clear options field
  useUpdateEffect(() => {
    if (selectedOption && !options.includes(selectedOption)) {
      setSelectedOption(null);
    }
  }, [JSON.stringify(options)]);

  // Trigger event handlers
  useUpdateEffect(() => {
    if (onChange || onBlur) {
      const fakeInputElement: InputObject = {
        value: listItems.map((item) => item.value),
        name,
      };
      onChange?.(createFakeChangeEventHandler(fakeInputElement));
      onBlur?.(createFakeBlurEventHandler(fakeInputElement));
    }
  }, [JSON.stringify(listItems)]);

  // Set ref
  useEffect(() => {
    const fakeInputElement = createFakeInputElement({
      value: listItems.map((item) => item.value),
      name,
    });
    setRef(inputRef, fakeInputElement);
  }, [inputRef, listItems, name]);

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const moveItem = (fromIndex: number, toIndex: number) => {
    setListItems(RA.move(fromIndex, toIndex, listItems));
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormControl
      component={Paper}
      elevation={2}
      sx={[
        { p: 2 },
        !!error && {
          border: "1px solid",
          borderColor: "error.main",
        },
      ]}
      error={error}
    >
      <Typography sx={[!!error && { color: "error.main" }]}>{label}</Typography>
      <Box sx={{ display: "flex", alignItems: "center", mt: 2 }}>
        <Autocomplete
          sx={{ mr: 2 }}
          value={selectedOption}
          fullWidth
          options={options}
          getOptionLabel={getOptionLabel}
          onChange={(_, value) => {
            setSelectedOption(value);
          }}
          autoHighlight
          renderInput={(params) => <StringFE {...params} sx={{ m: 0 }} variant="outlined" />}
        />
        <Button
          variant="contained"
          onClick={() => {
            setSelectedOption(null);
            if (selectedOption) {
              setListItems((items) => [...items, ...makeListItems([optionToItem(selectedOption)])]);
            }
          }}
          disabled={!selectedOption}
        >
          {t("button.add")}
        </Button>
      </Box>
      <List sx={{ pb: 0 }}>
        {listItems.map((item, index) => (
          <ListItem
            key={item.id}
            disableGutters
            secondaryAction={
              <>
                {index > 0 && (
                  <IconButton
                    size="small"
                    onClick={() => {
                      moveItem(index, index - 1);
                    }}
                  >
                    <ExpandLessIcon />
                  </IconButton>
                )}
                {index < listItems.length - 1 && (
                  <IconButton
                    size="small"
                    onClick={() => {
                      moveItem(index, index + 1);
                    }}
                  >
                    <ExpandMoreIcon />
                  </IconButton>
                )}
                <IconButton
                  size="small"
                  edge="end"
                  onClick={() => {
                    setListItems(listItems.filter(({ id }) => id !== item.id));
                  }}
                >
                  <RemoveCircleIcon />
                </IconButton>
              </>
            }
            disablePadding
            dense
          >
            <ListItemButton sx={{ cursor: "inherit" }} disableRipple>
              <ListItemText
                primary={getValueLabel(item.value)}
                title={getValueLabel(item.value)}
                sx={{
                  ".MuiTypography-root": {
                    textOverflow: "ellipsis",
                    overflow: "hidden",
                    whiteSpace: "nowrap",
                  },
                }}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
      {helperText && <FormHelperText>{helperText}</FormHelperText>}
    </FormControl>
  );
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const ListFEWithRHF = reactHookFormSupport({ defaultValue: [] as any })(ListFE);

// The HOC doesn't automatically forward component generics

export default ListFEWithRHF as <
  TItem,
  TOption,
  TFieldValues extends FieldValues = FieldValues,
  TFieldName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  TContext = any,
>(
  props: ReactHookFormSupportProps<TFieldValues, TFieldName, TContext> &
    ListFEProps<TItem, TOption>,
) => JSX.Element;
