import { AsyncThunk, EntitySelectors } from "@reduxjs/toolkit";
import { useEffect } from "react";
import { AppState } from "../ducks";
import { AppAsyncThunkConfig } from "../store";
import { AsyncEntityState, FetchStatus } from "../utils";
import useAppDispatch from "./useAppDispatch";
import useAppSelector from "./useAppSelector";

interface UseAsyncEntityStateParams<Entity, TSelected> {
  entityStateSelector: (state: AppState) => AsyncEntityState<Entity>;
  fetchAction: AsyncThunk<Entity[], undefined, AppAsyncThunkConfig>;
  valueSelector: (state: AppState) => TSelected;
}

interface UseAsyncEntityStateResponse<Entity, TSelected>
  extends Pick<AsyncEntityState<Entity>, "status" | "error"> {
  value: TSelected;
}

type Selectors<Entity> = EntitySelectors<Entity, AppState>;

function useAsyncAppSelector<
  Entity,
  TSelected = ReturnType<Selectors<Entity>[keyof Selectors<Entity>]>
>(
  params: UseAsyncEntityStateParams<Entity, TSelected>
): UseAsyncEntityStateResponse<Entity, TSelected> {
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
