import { Dispatch, SetStateAction, createContext } from "react";
import type { StudyMetadata } from "../../../../../../../../common/types";
import type { ScenarioBuilderConfig } from "./utils";

interface ScenarioBuilderContextType {
  config: ScenarioBuilderConfig;
  setConfig: Dispatch<SetStateAction<ScenarioBuilderConfig>>;
  refreshConfig: VoidFunction;
  activeRuleset: string;
  updateRuleset: (ruleset: string) => void;
  studyId: StudyMetadata["id"];
}

const defaultValues = {
  config: {},
  setConfig: () => undefined,
  refreshConfig: () => undefined,
  activeRuleset: "",
  updateRuleset: () => "",
  studyId: "",
};

export const ScenarioBuilderContext =
  createContext<ScenarioBuilderContextType>(defaultValues);
