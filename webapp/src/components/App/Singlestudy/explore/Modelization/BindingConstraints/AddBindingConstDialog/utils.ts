import { FieldValues } from "react-hook-form";
import CreateBindingConstraint from "../../../../Commands/Edition/commandTypes";

export type AddBindingConstType = FieldValues & typeof CreateBindingConstraint;
