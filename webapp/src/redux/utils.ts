import * as R from "ramda";

const APP_NAME = "antarest";

export const makeActionName = R.curry(
  (reducerName: string, actionType: string) =>
    `${APP_NAME}/${reducerName}/${actionType}`
);
