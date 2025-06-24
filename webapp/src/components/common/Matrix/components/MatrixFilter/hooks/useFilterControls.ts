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

import { useCallback, useState } from "react";
import type { FilterOperatorType, FilterState, FilterType, RowFilter } from "../types";

interface UseFilterControlsProps {
  filter: FilterState;
  setFilter: React.Dispatch<React.SetStateAction<FilterState>>;
  filterId?: string;
}

interface UseFilterControlsReturn {
  inputValue: string;
  setInputValue: React.Dispatch<React.SetStateAction<string>>;
  handleListChange: (value: string) => void;
  addValueToList: (filterId?: string) => void;
  addValuesToList: (values: number[], filterId?: string) => void;
  removeValueFromList: (valueToRemove: number, filterId?: string) => void;
  clearAllValues: (filterId?: string) => void;
  handleKeyPress: (event: React.KeyboardEvent) => void;
  handleCheckboxChange: (value: number, filterId?: string) => void;
  handleRangeChange: (newValue: number[], filterId?: string) => void;
  handleTypeChange: (newType: FilterType, filterId?: string) => void;
  handleOperatorChange: (newOperator: FilterOperatorType, filterId?: string) => void;
}

export function useFilterControls({
  setFilter,
  filterId,
}: UseFilterControlsProps): UseFilterControlsReturn {
  const [inputValue, setInputValue] = useState<string>("");

  const handleListChange = useCallback((value: string) => {
    setInputValue(value);
  }, []);

  // Handle adding a single value to the list filter
  const addValueToList = useCallback(
    (id?: string) => {
      const newValue = Number.parseInt(inputValue.trim(), 10);

      if (Number.isNaN(newValue)) {
        return;
      }

      if (id) {
        // For row filters
        setFilter((prevFilter) => {
          const rowFilter = prevFilter.rowsFilters.find((rf) => rf.id === id);
          if (!rowFilter || rowFilter.list?.includes(newValue)) {
            return prevFilter;
          }

          return {
            ...prevFilter,
            rowsFilters: prevFilter.rowsFilters.map((rf) => {
              if (rf.id !== id) {
                return rf;
              }
              return {
                ...rf,
                list: [...(rf.list || []), newValue].sort((a, b) => a - b),
              };
            }),
          };
        });
      } else {
        // For column filter
        setFilter((prevFilter) => {
          if (prevFilter.columnsFilter.list?.includes(newValue)) {
            return prevFilter;
          }

          return {
            ...prevFilter,
            columnsFilter: {
              ...prevFilter.columnsFilter,
              list: [...(prevFilter.columnsFilter.list || []), newValue].sort((a, b) => a - b),
            },
          };
        });
      }

      setInputValue("");
    },
    [inputValue, setFilter],
  );

  // Handle adding multiple values to the list filter (range)
  const addValuesToList = useCallback(
    (values: number[], id?: string) => {
      if (values.length === 0) {
        return;
      }

      if (id) {
        // For row filters
        setFilter((prevFilter) => {
          const rowFilter = prevFilter.rowsFilters.find((rf) => rf.id === id);
          if (!rowFilter) {
            return prevFilter;
          }

          const currentList = rowFilter.list || [];
          const newValues = values.filter((val) => !currentList.includes(val));

          if (newValues.length === 0) {
            return prevFilter;
          }

          return {
            ...prevFilter,
            rowsFilters: prevFilter.rowsFilters.map((rf) => {
              if (rf.id !== id) {
                return rf;
              }
              return {
                ...rf,
                list: [...currentList, ...newValues].sort((a, b) => a - b),
              };
            }),
          };
        });
      } else {
        // For column filter
        setFilter((prevFilter) => {
          const currentList = prevFilter.columnsFilter.list || [];
          const newValues = values.filter((val) => !currentList.includes(val));

          if (newValues.length === 0) {
            return prevFilter;
          }

          return {
            ...prevFilter,
            columnsFilter: {
              ...prevFilter.columnsFilter,
              list: [...currentList, ...newValues].sort((a, b) => a - b),
            },
          };
        });
      }
    },
    [setFilter],
  );

  // Handle removing a value from the list filter
  const removeValueFromList = useCallback(
    (valueToRemove: number, id?: string) => {
      if (id) {
        // For row filters
        setFilter((prevFilter) => ({
          ...prevFilter,
          rowsFilters: prevFilter.rowsFilters.map((rf) => {
            if (rf.id !== id) {
              return rf;
            }
            return {
              ...rf,
              list: (rf.list || []).filter((value) => value !== valueToRemove),
            };
          }),
        }));
      } else {
        // For column filter
        setFilter((prevFilter) => ({
          ...prevFilter,
          columnsFilter: {
            ...prevFilter.columnsFilter,
            list: (prevFilter.columnsFilter.list || []).filter((value) => value !== valueToRemove),
          },
        }));
      }
    },
    [setFilter],
  );

  // Handle checkbox changes for list filters
  // TODO: remove
  const handleCheckboxChange = useCallback(
    (value: number, id?: string) => {
      if (id) {
        // For row filters
        setFilter((prevFilter) => {
          const rowFilter = prevFilter.rowsFilters.find((rf) => rf.id === id);
          if (!rowFilter) {
            return prevFilter;
          }

          const currentList = rowFilter.list || [];
          const newList = currentList.includes(value)
            ? currentList.filter((item) => item !== value)
            : [...currentList, value].sort((a, b) => a - b);

          return {
            ...prevFilter,
            rowsFilters: prevFilter.rowsFilters.map((rf) => {
              if (rf.id !== id) {
                return rf;
              }
              return { ...rf, list: newList };
            }),
          };
        });
      } else {
        // For column filter
        setFilter((prevFilter) => {
          const currentList = prevFilter.columnsFilter.list || [];
          const newList = currentList.includes(value)
            ? currentList.filter((item) => item !== value)
            : [...currentList, value].sort((a, b) => a - b);

          return {
            ...prevFilter,
            columnsFilter: {
              ...prevFilter.columnsFilter,
              list: newList,
            },
          };
        });
      }
    },
    [setFilter],
  );

  // Handle range slider changes
  const handleRangeChange = useCallback(
    (newValue: number[], id?: string) => {
      if (id) {
        // For row filters
        setFilter((prevFilter) => ({
          ...prevFilter,
          rowsFilters: prevFilter.rowsFilters.map((rf) => {
            if (rf.id !== id) {
              return rf;
            }
            return {
              ...rf,
              range: { min: newValue[0], max: newValue[1] },
            };
          }),
        }));
      } else {
        // For column filter
        setFilter((prevFilter) => ({
          ...prevFilter,
          columnsFilter: {
            ...prevFilter.columnsFilter,
            range: {
              min: newValue[0],
              max: newValue[1],
            },
          },
        }));
      }
    },
    [setFilter],
  );

  const clearAllValues = useCallback(
    (id?: string) => {
      if (id) {
        // For row filters
        setFilter((prevFilter) => ({
          ...prevFilter,
          rowsFilters: prevFilter.rowsFilters.map((rf) => {
            if (rf.id !== id) {
              return rf;
            }
            return { ...rf, list: [] };
          }),
        }));
      } else {
        // For column filter
        setFilter((prevFilter) => ({
          ...prevFilter,
          columnsFilter: {
            ...prevFilter.columnsFilter,
            list: [],
          },
        }));
      }
    },
    [setFilter],
  );

  // Handle filter type changes
  const handleTypeChange = useCallback(
    (newType: FilterType, id?: string) => {
      if (id) {
        // For row filters
        setFilter((prevFilter) => ({
          ...prevFilter,
          rowsFilters: prevFilter.rowsFilters.map((rf) => {
            if (rf.id !== id) {
              return rf;
            }
            return { ...rf, type: newType } as RowFilter;
          }),
        }));
      } else {
        // For column filter
        setFilter((prevFilter) => ({
          ...prevFilter,
          columnsFilter: {
            ...prevFilter.columnsFilter,
            type: newType,
          },
        }));
      }
    },
    [setFilter],
  );

  const handleOperatorChange = useCallback(
    (newOperator: FilterOperatorType, id?: string) => {
      if (id) {
        // For row filters
        setFilter((prevFilter) => ({
          ...prevFilter,
          rowsFilters: prevFilter.rowsFilters.map((rf) => {
            if (rf.id !== id) {
              return rf;
            }
            return { ...rf, operator: newOperator } as RowFilter;
          }),
        }));
      } else {
        // For column filter
        setFilter((prevFilter) => ({
          ...prevFilter,
          columnsFilter: {
            ...prevFilter.columnsFilter,
            operator: newOperator,
          },
        }));
      }
    },
    [setFilter],
  );

  // Handle key presses for adding values
  const handleKeyPress = useCallback(
    (event: React.KeyboardEvent) => {
      if (event.key === "Enter" || event.key === ",") {
        event.preventDefault();
        addValueToList(filterId);
      }
    },
    [addValueToList, filterId],
  );

  return {
    inputValue,
    setInputValue,
    handleListChange,
    addValueToList,
    addValuesToList,
    removeValueFromList,
    clearAllValues,
    handleKeyPress,
    handleCheckboxChange,
    handleRangeChange,
    handleTypeChange,
    handleOperatorChange,
  };
}
