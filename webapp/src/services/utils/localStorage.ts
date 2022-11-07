import * as RA from "ramda-adjunct";
import packages from "../../../package.json";
import { UserInfo } from "../../common/types";
import { TableTemplate } from "../../components/App/Singlestudy/explore/Modelization/TableMode/utils";
import {
  StudiesSortConf,
  StudiesState,
  StudyFilters,
} from "../../redux/ducks/studies";

export enum StorageKey {
  Version = "version",
  AuthUser = "authUser",
  // Studies
  StudiesFavorites = "studies.favorites",
  StudiesFilters = "studies.filters",
  StudiesSort = "studies.sort",
  StudiesModelTableModeTemplates = "studies.model.tableMode.templates",
}

const APP_NAME = packages.name;
const SHARED_KEYS = [StorageKey.Version, StorageKey.AuthUser];

interface TypeFromKey {
  [StorageKey.Version]: string;
  [StorageKey.AuthUser]: UserInfo;
  [StorageKey.StudiesFavorites]: StudiesState["favorites"];
  [StorageKey.StudiesFilters]: Partial<StudyFilters>;
  [StorageKey.StudiesSort]: Partial<StudiesSortConf>;
  [StorageKey.StudiesModelTableModeTemplates]: Omit<TableTemplate, "id">[];
}

function formalizeKey(key: StorageKey): string {
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

function getItem<T extends StorageKey>(key: T): TypeFromKey[T] | null {
  try {
    const serializedState = localStorage.getItem(formalizeKey(key));
    if (serializedState === null) {
      return null;
    }
    return JSON.parse(serializedState);
  } catch (err) {
    return null;
  }
}

function setItem<T extends StorageKey>(
  key: T,
  data: TypeFromKey[T] | ((prev: TypeFromKey[T] | null) => TypeFromKey[T])
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

function removeItem(key: StorageKey): void {
  try {
    localStorage.removeItem(formalizeKey(key));
  } catch {
    // Empty
  }
}

export default { getItem, setItem, removeItem };
