import { createContext } from "react";

interface CxType {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  config: Record<string, any>;
  currentRuleset: string;
  setCurrentRuleset: React.Dispatch<React.SetStateAction<string>>;
}

export default createContext<CxType>({} as CxType);
