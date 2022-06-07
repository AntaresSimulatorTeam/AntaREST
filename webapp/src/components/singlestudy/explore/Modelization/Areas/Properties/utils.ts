import { FieldElement, FieldsInfo } from "./common";

export interface PropertiesFields extends FieldsInfo {
  name: FieldElement<string>;
  color: FieldElement<{ r: number; g: number; b: number }>;
  posX: FieldElement<number>;
  posY: FieldElement<number>;
  energieCostUnsupplied: FieldElement<number>;
  energieCostSpilled: FieldElement<number>;
  nonDispatchPower: FieldElement<boolean>;
  dispatchHydroPower: FieldElement<boolean>;
  otherDispatchPower: FieldElement<boolean>;
}

export const defaultPath: PropertiesFields = {
  name: { path: "" },
  color: { path: "" },
  posX: { path: "" },
  posY: { path: "" },
  energieCostUnsupplied: { path: "" },
  energieCostSpilled: { path: "" },
  nonDispatchPower: { path: "" },
  dispatchHydroPower: { path: "" },
  otherDispatchPower: { path: "" },
};

export default {};
