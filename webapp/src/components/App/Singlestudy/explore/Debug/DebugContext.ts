import { createContext } from "react";
import type { FileInfo } from "./utils";
import { voidFn } from "../../../../../utils/fnUtils";

const initialDebugContextValue = {
  onFileSelect: voidFn<[FileInfo]>,
  reloadTreeData: voidFn,
};

const DebugContext = createContext(initialDebugContextValue);

export default DebugContext;
