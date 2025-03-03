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

import * as RA from "ramda-adjunct";
import packages from "../../../package.json";
import type { UserInfo } from "../../types/types";
import type { TableTemplate } from "../../components/App/Singlestudy/explore/TableModeList/utils";
import type { StudiesSortConf, StudiesState } from "../../redux/ducks/studies";
import type { UIState } from "../../redux/ducks/ui";
import { TABLE_MODE_TYPES_ALIASES } from "../api/studies/tableMode/constants";

export const StorageKey = {
  Version: "version",
  AuthUser: "authUser",
  // Studies
  StudiesFavorites: "studies.favorites",
  StudiesSort: "studies.sort",
  StudiesModelTableModeTemplates: "studies.model.tableMode.templates",
  // UI
  UIMenuCollapsed: "ui.menuCollapsed",
} as const;

type Key = (typeof StorageKey)[keyof typeof StorageKey] | string;

const APP_NAME = packages.name;
const SHARED_KEYS = [StorageKey.Version, StorageKey.AuthUser];

interface TypeFromKey {
  [StorageKey.Version]: string;
  [StorageKey.AuthUser]: UserInfo;
  [StorageKey.StudiesFavorites]: StudiesState["favorites"];
  [StorageKey.StudiesSort]: Partial<StudiesSortConf>;
  [StorageKey.StudiesModelTableModeTemplates]: Array<Omit<TableTemplate, "id">>;
  [StorageKey.UIMenuCollapsed]: UIState["menuOpen"];
  [key: string]: unknown;
}

function formalizeKey(key: Key): string {
  if (SHARED_KEYS.includes(key)) {
    return `${APP_NAME}.${key}`;
  }
  const authUser = getItem(StorageKey.AuthUser);
  // Authentication may not be required
  if (authUser === null) {
    return `${APP_NAME}.${key}`;
  }
  return `${APP_NAME}.${authUser.id}.${key}`;
}

function getItem<T extends Key>(key: T): TypeFromKey[T] | null {
  try {
    const serializedState = localStorage.getItem(formalizeKey(key));
    if (serializedState === null) {
      return null;
    }
    const res = JSON.parse(serializedState);

    // Convert deprecated types to new ones (breaking change from v2.16.8)
    if (key === StorageKey.StudiesModelTableModeTemplates) {
      return res.map((template: Record<string, unknown>) => ({
        ...template,
        // @ts-expect-error To ignore error TS2551
        type: TABLE_MODE_TYPES_ALIASES[template.type] ?? template.type,
      }));
    }

    return res;
  } catch {
    return null;
  }
}

function setItem<T extends Key>(
  key: T,
  data: TypeFromKey[T] | ((prev: TypeFromKey[T] | null) => TypeFromKey[T]),
): void {
  try {
    if (RA.isFunction(data)) {
      const prev = getItem(key);
      localStorage.setItem(formalizeKey(key), JSON.stringify(data(prev)));
      return;
    }
    localStorage.setItem(formalizeKey(key), JSON.stringify(data));
  } catch {
    // Empty
  }
}

function removeItem(key: Key): void {
  try {
    localStorage.removeItem(formalizeKey(key));
  } catch {
    // Empty
  }
}

export default { getItem, setItem, removeItem };
