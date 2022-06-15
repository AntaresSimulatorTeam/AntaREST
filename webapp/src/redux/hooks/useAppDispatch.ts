import { useDispatch } from "react-redux";
import { AppDispatch } from "../store";

// eslint-disable-next-line @typescript-eslint/explicit-function-return-type
const useAppDispatch = () => useDispatch<AppDispatch>();

export default useAppDispatch;
