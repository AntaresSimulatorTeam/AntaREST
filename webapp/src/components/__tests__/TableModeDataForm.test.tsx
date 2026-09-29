/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import userEvent from "@testing-library/user-event";
import { render, screen, waitFor } from "@testing-library/react";
import { thermalKeys } from "@/queries/thermals/keys";
import { renewableKeys } from "@/queries/renewables/keys";
import { storageKeys } from "@/queries/storages/keys";
import { getTableModeData, setTableModeData } from "@/services/api/studies/tableMode";
import type { TableModeData } from "@/services/api/studies/tableMode/types";
import type { SubmitHandlerPlus } from "../Form/types";
import TableModeDataForm from "../TableModeDataForm";

const { submitted, failed } = vi.hoisted(() => ({ submitted: vi.fn(), failed: vi.fn() }));
vi.mock("@/services/api/client", () => ({ default: {} }));
vi.mock("@/i18n", () => ({ default: { t: (key: string) => key, language: "en" } }));
vi.mock("@/services/api/studies/tableMode", () => ({
  getTableModeData: vi.fn(),
  setTableModeData: vi.fn(),
}));
vi.mock("@/redux/hooks/useAppDispatch", () => ({ default: () => vi.fn() }));
vi.mock("@/redux/ducks/studySyntheses", () => ({ setStudySynthesis: vi.fn() }));
vi.mock("react-i18next", () => ({ useTranslation: () => ({ t: (key: string) => key }) }));
vi.mock("../DataGridSkeleton", () => ({ default: () => null }));
vi.mock("../DataGridForm", () => ({
  default: ({
    defaultData,
    onSubmit,
  }: {
    defaultData: TableModeData;
    onSubmit: (data: SubmitHandlerPlus<TableModeData>) => Promise<void>;
  }) => (
    <button
      onClick={() => {
        Promise.resolve(onSubmit({ values: defaultData, dirtyValues: defaultData }))
          .then(submitted)
          .catch(failed);
      }}
    >
      Save
    </button>
  ),
}));

let client: QueryClient;
beforeEach(() => {
  vi.clearAllMocks();
  client = new QueryClient({ defaultOptions: { queries: { staleTime: Infinity, retry: false } } });
  vi.mocked(getTableModeData).mockResolvedValue({
    "area-1 / cluster": { enabled: false },
    "area-1 / other-cluster": { enabled: false },
    "area-2 / cluster": { enabled: false },
  });
  vi.mocked(setTableModeData).mockResolvedValue(undefined);
});
afterEach(() => client.clear());

test.each([
  { type: "thermals" as const, keys: thermalKeys, otherKeys: renewableKeys },
  { type: "renewables" as const, keys: renewableKeys, otherKeys: thermalKeys },
  { type: "st-storages" as const, keys: storageKeys, otherKeys: thermalKeys },
])(
  "$type save refreshes a fresh cached list when returning to the view",
  async ({ type, keys, otherKeys }) => {
    let enabled = true;
    const read = vi.fn(() => Promise.resolve([{ id: "cluster", enabled }]));
    const options = { queryKey: keys.list("study", "area-1"), queryFn: read };
    await client.fetchQuery(options);
    const secondArea = keys.list("study", "area-2");
    client.setQueryData(secondArea, []);
    const untouched = [
      keys.list("study", "area-3"),
      keys.list("other-study", "area-1"),
      otherKeys.list("study", "area-1"),
    ];
    untouched.forEach((key) => {
      client.setQueryData(key, []);
    });
    vi.mocked(setTableModeData).mockImplementation(() => {
      enabled = false;
      return Promise.resolve();
    });

    const view = render(
      <QueryClientProvider client={client}>
        <TableModeDataForm studyId="study" type={type} columns={["enabled"]} />
      </QueryClientProvider>,
    );
    await userEvent.click(await screen.findByRole("button", { name: "Save" }));
    await waitFor(() => expect(submitted).toHaveBeenCalled());
    expect(setTableModeData).toHaveBeenCalledWith(
      {
        studyId: "study",
        tableType: type,
        data: {
          "area-1 / cluster": { enabled: false },
          "area-1 / other-cluster": { enabled: false },
          "area-2 / cluster": { enabled: false },
        },
      },
      expect.anything(),
    );
    view.unmount();

    expect(await client.fetchQuery(options)).toEqual([{ id: "cluster", enabled: false }]);
    expect(read).toHaveBeenCalledTimes(2);
    expect(client.getQueryState(secondArea)?.isInvalidated).toBe(true);
    untouched.forEach((key) => {
      expect(client.getQueryState(key)?.isInvalidated).toBe(false);
    });
  },
);

test("a rejected Table Mode save does not invalidate cached clusters", async () => {
  const key = thermalKeys.list("study", "area-1");
  client.setQueryData(key, [{ enabled: true }]);
  vi.mocked(setTableModeData).mockRejectedValueOnce(new Error("save failed"));
  render(
    <QueryClientProvider client={client}>
      <TableModeDataForm studyId="study" type="thermals" columns={["enabled"]} />
    </QueryClientProvider>,
  );
  await userEvent.click(await screen.findByRole("button", { name: "Save" }));
  await waitFor(() => expect(failed).toHaveBeenCalled());
  expect(client.getQueryState(key)?.isInvalidated).toBe(false);
  expect(client.getQueryData(key)).toEqual([{ enabled: true }]);
});
