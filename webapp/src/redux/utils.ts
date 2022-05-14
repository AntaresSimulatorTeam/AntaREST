import * as R from "ramda";

const APP_NAME = "antarest";

export enum Status {
  Idle = "idle",
  Loading = "loading",
  Succeeded = "succeeded",
  Failed = "failed",
}

export const makeActionName = R.curry(
  (reducerName: string, actionType: string) =>
    `${APP_NAME}/${reducerName}/${actionType}`
);
