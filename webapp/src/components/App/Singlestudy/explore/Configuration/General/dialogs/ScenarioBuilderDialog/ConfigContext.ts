import { createContext } from "react";
import { StudyMetadata } from "../../../../../../../../common/types";
import { ScenarioBuilderConfig } from "./utils";

interface CxType {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  config: Record<string, any>;
  setConfig: React.Dispatch<React.SetStateAction<ScenarioBuilderConfig>>;
  reloadConfig: VoidFunction;
  activeRuleset: string;
  setActiveRuleset: (ruleset: string) => void;
  studyId: StudyMetadata["id"];
}

export default createContext<CxType>({} as CxType);
