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

import { produce } from "immer";
import { useCallback, useState } from "react";
import type { FilterOperatorType, FilterState, FilterType } from "../types";

interface UseFilterControlsProps {
  filter: FilterState;
  setFilter: React.Dispatch<React.SetStateAction<FilterState>>;
  filterId?: string;
}

interface UseFilterControlsReturn {
  inputValue: string;
  setInputValue: React.Dispatch<React.SetStateAction<string>>;
  handleListChange: (value: string) => void;
  addValueToRowFilter: (filterId: string) => void;
  addValueToColumnFilter: () => void;
  addValuesToRowFilter: (values: number[], filterId: string) => void;
  addValuesToColumnFilter: (values: number[]) => void;
  removeValueFromRowFilter: (valueToRemove: number, filterId: string) => void;
  removeValueFromColumnFilter: (valueToRemove: number) => void;
  clearRowFilterValues: (filterId: string) => void;
  clearColumnFilterValues: () => void;
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

  const addValueToRowFilter = useCallback(
    (filterId: string) => {
      const newValue = Number.parseInt(inputValue.trim(), 10);

      if (Number.isNaN(newValue)) {
        return;
      }

      setFilter(
        produce((draft) => {
          const rowFilter = draft.rowsFilters.find((rf) => rf.id === filterId);

          if (!rowFilter || rowFilter.list?.includes(newValue)) {
            return;
          }

          if (!rowFilter.list) {
            rowFilter.list = [];
          }

          rowFilter.list.push(newValue);
          rowFilter.list.sort((a, b) => a - b);
        }),
      );

      setInputValue("");
    },
    [inputValue, setFilter],
  );

  const addValueToColumnFilter = useCallback(() => {
    const newValue = Number.parseInt(inputValue.trim(), 10);

    if (Number.isNaN(newValue)) {
      return;
    }

    setFilter(
      produce((draft) => {
        if (draft.columnsFilter.list?.includes(newValue)) {
          return;
        }

        if (!draft.columnsFilter.list) {
          draft.columnsFilter.list = [];
        }

        draft.columnsFilter.list.push(newValue);
        draft.columnsFilter.list.sort((a, b) => a - b);
      }),
    );

    setInputValue("");
  }, [inputValue, setFilter]);

  // Handle adding multiple values to the row filter (range)
  const addValuesToRowFilter = useCallback(
    (values: number[], filterId: string) => {
      if (values.length === 0) {
        return;
      }

      setFilter(
        produce((draft) => {
          const rowFilter = draft.rowsFilters.find((rf) => rf.id === filterId);

          if (!rowFilter) {
            return;
          }

          const currentList = rowFilter.list || [];
          const newValues = values.filter((val) => !currentList.includes(val));

          if (newValues.length === 0) {
            return;
          }

          if (!rowFilter.list) {
            rowFilter.list = [];
          }

          rowFilter.list.push(...newValues);
          rowFilter.list.sort((a, b) => a - b);
        }),
      );
    },
    [setFilter],
  );

  // Handle adding multiple values to the column filter (range)
  const addValuesToColumnFilter = useCallback(
    (values: number[]) => {
      if (values.length === 0) {
        return;
      }

      setFilter(
        produce((draft) => {
          const currentList = draft.columnsFilter.list || [];
          const newValues = values.filter((val) => !currentList.includes(val));

          if (newValues.length === 0) {
            return;
          }

          if (!draft.columnsFilter.list) {
            draft.columnsFilter.list = [];
          }

          draft.columnsFilter.list.push(...newValues);
          draft.columnsFilter.list.sort((a, b) => a - b);
        }),
      );
    },
    [setFilter],
  );

  const removeValueFromRowFilter = useCallback(
    (valueToRemove: number, filterId: string) => {
      setFilter(
        produce((draft) => {
          const rowFilter = draft.rowsFilters.find((rf) => rf.id === filterId);

          if (rowFilter?.list) {
            rowFilter.list = rowFilter.list.filter((value) => value !== valueToRemove);
          }
        }),
      );
    },
    [setFilter],
  );

  const removeValueFromColumnFilter = useCallback(
    (valueToRemove: number) => {
      setFilter(
        produce((draft) => {
          if (draft.columnsFilter.list) {
            draft.columnsFilter.list = draft.columnsFilter.list.filter(
              (value) => value !== valueToRemove,
            );
          }
        }),
      );
    },
    [setFilter],
  );

  // Handle checkbox changes for list filters
  const handleCheckboxChange = useCallback(
    (value: number, id?: string) => {
      if (id) {
        // For row filters
        setFilter(
          produce((draft) => {
            const rowFilter = draft.rowsFilters.find((rf) => rf.id === id);

            if (!rowFilter) {
              return;
            }

            if (!rowFilter.list) {
              rowFilter.list = [];
            }

            const currentIndex = rowFilter.list.indexOf(value);

            if (currentIndex >= 0) {
              rowFilter.list.splice(currentIndex, 1);
            } else {
              rowFilter.list.push(value);
              rowFilter.list.sort((a, b) => a - b);
            }
          }),
        );
      } else {
        // For column filter
        setFilter(
          produce((draft) => {
            if (!draft.columnsFilter.list) {
              draft.columnsFilter.list = [];
            }

            const currentIndex = draft.columnsFilter.list.indexOf(value);

            if (currentIndex >= 0) {
              draft.columnsFilter.list.splice(currentIndex, 1);
            } else {
              draft.columnsFilter.list.push(value);
              draft.columnsFilter.list.sort((a, b) => a - b);
            }
          }),
        );
      }
    },
    [setFilter],
  );

  // Handle range slider changes
  const handleRangeChange = useCallback(
    (newValue: number[], id?: string) => {
      if (id) {
        // For row filters
        setFilter(
          produce((draft) => {
            const rowFilter = draft.rowsFilters.find((rf) => rf.id === id);

            if (rowFilter) {
              rowFilter.range = { min: newValue[0], max: newValue[1] };
            }
          }),
        );
      } else {
        // For column filter
        setFilter(
          produce((draft) => {
            draft.columnsFilter.range = { min: newValue[0], max: newValue[1] };
          }),
        );
      }
    },
    [setFilter],
  );

  const clearRowFilterValues = useCallback(
    (filterId: string) => {
      setFilter(
        produce((draft) => {
          const rowFilter = draft.rowsFilters.find((rf) => rf.id === filterId);

          if (rowFilter) {
            rowFilter.list = [];
          }
        }),
      );
    },
    [setFilter],
  );

  const clearColumnFilterValues = useCallback(() => {
    setFilter(
      produce((draft) => {
        draft.columnsFilter.list = [];
      }),
    );
  }, [setFilter]);

  // Handle filter type changes
  const handleTypeChange = useCallback(
    (newType: FilterType, id?: string) => {
      if (id) {
        // For row filters
        setFilter(
          produce((draft) => {
            const rowFilter = draft.rowsFilters.find((rf) => rf.id === id);

            if (rowFilter) {
              rowFilter.type = newType;
            }
          }),
        );
      } else {
        // For column filter
        setFilter(
          produce((draft) => {
            draft.columnsFilter.type = newType;
          }),
        );
      }
    },
    [setFilter],
  );

  const handleOperatorChange = useCallback(
    (newOperator: FilterOperatorType, id?: string) => {
      if (id) {
        // For row filters
        setFilter(
          produce((draft) => {
            const rowFilter = draft.rowsFilters.find((rf) => rf.id === id);

            if (rowFilter) {
              rowFilter.operator = newOperator;
            }
          }),
        );
      } else {
        // For column filter
        setFilter(
          produce((draft) => {
            draft.columnsFilter.operator = newOperator;
          }),
        );
      }
    },
    [setFilter],
  );

  // Handle key presses for adding values
  const handleKeyPress = useCallback(
    (event: React.KeyboardEvent) => {
      if (event.key === "Enter" || event.key === ",") {
        event.preventDefault();
        if (filterId) {
          addValueToRowFilter(filterId);
        } else {
          addValueToColumnFilter();
        }
      }
    },
    [addValueToRowFilter, addValueToColumnFilter, filterId],
  );

  return {
    inputValue,
    setInputValue,
    handleListChange,
    addValueToRowFilter,
    addValueToColumnFilter,
    addValuesToRowFilter,
    addValuesToColumnFilter,
    removeValueFromRowFilter,
    removeValueFromColumnFilter,
    clearRowFilterValues,
    clearColumnFilterValues,
    handleKeyPress,
    handleCheckboxChange,
    handleRangeChange,
    handleTypeChange,
    handleOperatorChange,
  };
}
