import { Dispatch, SetStateAction, createContext } from "react";
import type { StudyMetadata } from "../../../../../../../../common/types";
import type { ScenarioBuilderConfig } from "./utils";

interface ScenarioBuilderContextType {
  config: ScenarioBuilderConfig;
  setConfig: Dispatch<SetStateAction<ScenarioBuilderConfig>>;
  refreshConfig: VoidFunction;
  isConfigLoading: boolean;
  studyId: StudyMetadata["id"];
}

const defaultValues = {
  config: {},
  setConfig: () => undefined,
  refreshConfig: () => undefined,
  isConfigLoading: true,
  studyId: "",
};

export const ScenarioBuilderContext =
  createContext<ScenarioBuilderContextType>(defaultValues);
