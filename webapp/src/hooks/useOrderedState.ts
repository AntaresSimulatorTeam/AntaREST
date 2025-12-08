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
import { v4 as uuidv4 } from "uuid";

interface OrderedState<T> {
  byId: Record<string, T>;
  order: string[];
}

type InitialState<T> = T[] | (() => T[]);

function convertInitialState<T>(initialState?: InitialState<T>): OrderedState<T> {
  if (!initialState) {
    return { byId: {}, order: [] };
  }

  if (typeof initialState === "function") {
    return convertInitialState(initialState());
  }

  const byId: Record<string, T> = {};
  const order: string[] = [];

  initialState.forEach((item) => {
    const id = uuidv4();
    byId[id] = item;
    order.push(id);
  });

  return { byId, order };
}

function useOrderedState<T>(initialState?: InitialState<T>) {
  const [state, setState] = useState(() => convertInitialState(initialState));

  const getItem = useCallback(
    (itemId: string) => {
      return state.byId[itemId];
    },
    [state],
  );

  const addItem = useCallback((item: T) => {
    const id = uuidv4();

    setState((prev) => ({
      byId: { ...prev.byId, [id]: item },
      order: [...prev.order, id],
    }));

    return id;
  }, []);

  const removeItem = useCallback((itemId: string) => {
    setState((prev) => {
      const { [itemId]: ignore, ...rest } = prev.byId;

      return {
        byId: rest,
        order: prev.order.filter((id) => id !== itemId),
      };
    });
  }, []);

  const mapItems = useCallback(
    <R>(callback: (item: T, id: string) => R): R[] => {
      return state.order.map((id) => callback(state.byId[id], id));
    },
    [state],
  );

  return {
    getItem,
    addItem,
    removeItem,
    mapItems,
  };
}

export default useOrderedState;
