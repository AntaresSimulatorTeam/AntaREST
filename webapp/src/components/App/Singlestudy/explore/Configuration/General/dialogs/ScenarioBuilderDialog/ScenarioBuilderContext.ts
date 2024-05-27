import { createContext } from "react";
import type { StudyMetadata } from "../../../../../../../../common/types";
import type { ScenarioBuilderConfig } from "./utils";

interface ScenarioBuilderContextType {
  config: ScenarioBuilderConfig;
  studyId: StudyMetadata["id"];
}

const defaultValues = {
  config: {},
  studyId: "",
};

export const ScenarioBuilderContext =
  createContext<ScenarioBuilderContextType>(defaultValues);
