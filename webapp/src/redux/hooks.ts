import { TypedUseSelectorHook, useDispatch, useSelector } from "react-redux";
import { AppState } from "./ducks";
import { AppDispatch } from "./store";

// eslint-disable-next-line @typescript-eslint/explicit-function-return-type
export const useAppDispatch = () => useDispatch<AppDispatch>();

export const useAppSelector: TypedUseSelectorHook<AppState> = useSelector;
