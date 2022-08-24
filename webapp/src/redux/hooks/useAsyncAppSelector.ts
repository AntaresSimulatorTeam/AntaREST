import { AsyncThunk } from "@reduxjs/toolkit";
import { useEffect } from "react";
import { AppState } from "../ducks";
import { AppAsyncThunkConfig } from "../store";
import { AsyncEntityState, FetchStatus } from "../utils";
import useAppDispatch from "./useAppDispatch";
import useAppSelector from "./useAppSelector";

interface UseAsyncEntityStateParams<Entity, Selected> {
  entityStateSelector: (state: AppState) => AsyncEntityState<Entity>;
  fetchAction: AsyncThunk<Entity[], undefined, AppAsyncThunkConfig>;
  valueSelector: (state: AppState) => Selected;
}

export interface UseAsyncEntityStateResponse<Entity, Selected>
  extends Pick<AsyncEntityState<Entity>, "status" | "error"> {
  value: Selected;
}

function useAsyncAppSelector<Entity, Selected>(
  params: UseAsyncEntityStateParams<Entity, Selected>
): UseAsyncEntityStateResponse<Entity, Selected> {
  const { entityStateSelector, fetchAction, valueSelector } = params;
  const status = useAppSelector((state) => entityStateSelector(state).status);
  const error = useAppSelector((state) => entityStateSelector(state).error);
  const value = useAppSelector(valueSelector);
  const dispatch = useAppDispatch();

  useEffect(() => {
    if (status === FetchStatus.Idle) {
      dispatch(fetchAction());
    }
  }, [dispatch, fetchAction, status]);

  return { status, error, value };
}

export default useAsyncAppSelector;
