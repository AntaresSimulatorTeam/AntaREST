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
  ListItemIcon,
  ListItemText,
  Paper,
  setRef,
  Typography,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import RemoveCircleIcon from "@mui/icons-material/RemoveCircle";
import { useEffect, useId, useState } from "react";
import {
  DragDropContext,
  Droppable,
  Draggable,
  DropResult,
} from "react-beautiful-dnd";
import DragHandleIcon from "@mui/icons-material/DragHandle";
import * as RA from "ramda-adjunct";
import { useUpdateEffect } from "react-use";
import { FieldPath, FieldValues } from "react-hook-form";
import StringFE from "../StringFE";
import reactHookFormSupport, {
  ReactHookFormSupportProps,
} from "../../../../hoc/reactHookFormSupport";
import {
  createFakeBlurEventHandler,
  createFakeChangeEventHandler,
  FakeBlurEventHandler,
  FakeChangeEventHandler,
  FakeHTMLInputElement,
} from "../../../../utils/feUtils";
import { makeLabel, makeListItems } from "./utils";

interface ListFEProps<TItem, TOption> {
  defaultValue?: ReadonlyArray<TItem>;
  value?: ReadonlyArray<TItem>;
  options: ReadonlyArray<TOption>;
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
    options,
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
  const [listItems, setListItems] = useState(() =>
    makeListItems(value || defaultValue || [])
  );
  const [selectedOption, setSelectedOption] = useState<TOption | null>(null);
  const droppableId = useId();

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
      const fakeInputElement: FakeHTMLInputElement = {
        value: listItems.map((item) => item.value),
        name,
      };
      onChange?.(createFakeChangeEventHandler(fakeInputElement));
      onBlur?.(createFakeBlurEventHandler(fakeInputElement));
    }
  }, [JSON.stringify(listItems)]);

  // Set ref
  useEffect(() => {
    const fakeInputElement: FakeHTMLInputElement = {
      value: listItems.map((item) => item.value),
      name,
    };
    setRef(inputRef, fakeInputElement);
  }, [inputRef, listItems, name]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const onItemDragEnd = (result: DropResult) => {
    const { source, destination } = result;
    // It's null if dropped outside the list
    if (destination) {
      setListItems(RA.move(source.index, destination.index, listItems));
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormControl
      component={Paper}
      sx={[
        {
          p: 2,
          backgroundImage:
            "linear-gradient(rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.05))",
        },
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
          renderInput={(params) => (
            <StringFE
              {...params}
              sx={{ m: 0 }}
              size="small"
              variant="outlined"
            />
          )}
        />
        <Button
          variant="contained"
          size="small"
          onClick={() => {
            setSelectedOption(null);
            if (selectedOption) {
              setListItems((items) => [
                ...items,
                ...makeListItems([optionToItem(selectedOption)]),
              ]);
            }
          }}
          disabled={!selectedOption}
        >
          {t("button.add")}
        </Button>
      </Box>
      <DragDropContext onDragEnd={onItemDragEnd}>
        <Droppable droppableId={droppableId}>
          {(provided) => (
            <List
              {...provided.droppableProps}
              ref={provided.innerRef}
              sx={{ pb: 0 }}
            >
              {listItems.map((item, index) => (
                <Draggable key={item.id} draggableId={item.id} index={index}>
                  {(provided, snapshot) => (
                    <ListItem
                      key={item.id}
                      {...provided.draggableProps}
                      {...provided.dragHandleProps}
                      sx={[
                        {
                          ...provided.draggableProps.style,
                        },
                        snapshot.isDragging && {
                          background: "rgba(255, 255, 255, 0.32)", // Like hover color
                        },
                      ]}
                      ref={provided.innerRef}
                      secondaryAction={
                        <IconButton
                          edge="end"
                          onClick={() => {
                            setListItems(
                              listItems.filter(({ id }) => id !== item.id)
                            );
                          }}
                        >
                          <RemoveCircleIcon />
                        </IconButton>
                      }
                      disablePadding
                      dense
                    >
                      <ListItemButton
                        sx={{ cursor: "inherit" }}
                        disableRipple
                        disableGutters
                      >
                        <ListItemIcon sx={{ minWidth: 0, pr: 2, pl: 1 }}>
                          <DragHandleIcon />
                        </ListItemIcon>
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
                  )}
                </Draggable>
              ))}
              {provided.placeholder}
            </List>
          )}
        </Droppable>
      </DragDropContext>
      {helperText && <FormHelperText>{helperText}</FormHelperText>}
    </FormControl>
  );
}

// TODO find a clean solution to support generics

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export default reactHookFormSupport({ defaultValue: [] as any })(ListFE) as <
  TItem,
  TOption,
  TFieldValues extends FieldValues = FieldValues,
  TFieldName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  TContext = any
>(
  props: ReactHookFormSupportProps<TFieldValues, TFieldName, TContext> &
    ListFEProps<TItem, TOption>
) => JSX.Element;
