import { createContext, useContext } from "react";
import type { File } from "./utils";
import { voidFn } from "../../../../../utils/fnUtils";

const initialDebugContextValue = {
  onFileSelect: voidFn<[File]>,
  reloadTreeData: voidFn,
};

const DebugContext = createContext(initialDebugContextValue);

export const useDebugContext = (): typeof initialDebugContextValue =>
  useContext(DebugContext);

export default DebugContext;
