import { TypedUseSelectorHook, useSelector } from "react-redux";
import { AppState } from "../ducks";

const useAppSelector: TypedUseSelectorHook<AppState> = useSelector;

export default useAppSelector;
