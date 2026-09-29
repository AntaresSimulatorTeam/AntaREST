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

import { ThemeProvider } from "@mui/material";
import theme from "@/theme";
import { Route as TableRoute } from "../../index";
import type { RowData } from "@/components/GroupedDataTable/types";
import { Suspense } from "react";
import { thermalKeys } from "@/queries/thermals/keys";
import * as api from "@/services/api/studies/areas/thermals";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, renderHook, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route as ParametersRoute } from "../../$thermalId/parameters";
import useThermalClusters from "../useThermalClusters";
import useThermalClusterDefaults from "../useThermalClusterDefaults";
import { cluster, deferred } from "./fixtures";
import type { ThermalCluster } from "@/services/api/studies/areas/thermals/types";

const { params, notify, dispatch, t } = vi.hoisted(() => ({
  params: { studyId: "study", areaId: "area", thermalId: "gas" },
  notify: vi.fn(),
  dispatch: vi.fn(),
  t: (key: string) => key,
}));
vi.mock("@/services/api/client", () => ({ default: {} }));
vi.mock("@/i18n", () => ({ default: { t: (key: string) => key, language: "en" } }));
vi.mock("@/services/api/studies/areas/thermals");
vi.mock("@/redux/hooks/useAppDispatch", () => ({ default: () => dispatch }));
vi.mock("@/redux/ducks/studySyntheses", () => ({ setStudySynthesis: vi.fn() }));
vi.mock("@/hooks/useFormBlocker", () => ({ default: vi.fn() }));
vi.mock("@/hooks/useEnqueueErrorSnackbar", () => ({ default: () => notify }));
vi.mock("@/routes/_authenticated/studies/$studyId/-hooks/useStudy", () => ({
  default: () => ({ id: params.studyId, version: "9.3.0" }),
}));
vi.mock("@tanstack/react-router", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@tanstack/react-router")>()),
  createFileRoute: () => (options: object) => ({ options, useParams: () => params }),
}));
vi.mock("react-i18next", () => ({ useTranslation: () => ({ t }) }));
vi.mock("@/components/CustomScrollbar", () => ({
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/components/router/RouterLink", () => ({
  default: ({ children }: { children: React.ReactNode }) => <a>{children}</a>,
}));
vi.mock("@/components/GroupedDataTable/CreateDialog", () => ({
  default: ({ onSubmit }: { onSubmit: (row: RowData) => Promise<void> }) => (
    <button onClick={() => onSubmit({ name: "New", group: "gas" })}>Confirm create</button>
  ),
}));
vi.mock("@/components/dialogs/ConfirmationDialog", () => ({
  default: ({ onConfirm }: { onConfirm: () => Promise<void> }) => (
    <button onClick={onConfirm}>Confirm delete</button>
  ),
}));

function Table() {
  const Component = TableRoute.options.component;
  if (!Component) {
    throw new Error("Missing table component");
  }
  return (
    <ThemeProvider theme={theme}>
      <Component />
    </ThemeProvider>
  );
}

let client: QueryClient;
function wrapper({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={client}>
      <Suspense fallback={null}>{children}</Suspense>
    </QueryClientProvider>
  );
}
function Parameters() {
  const Component = ParametersRoute.options.component;
  if (!Component) {
    throw new Error("Missing parameters component");
  }
  return <Component />;
}
const scope = { studyId: "study", areaId: "area" };
const key = thermalKeys.list("study", "area");
const capacityLabel = "study.modeling.clusters.nominalCapacity";

beforeEach(() => {
  vi.clearAllMocks();
  params.thermalId = "gas";
  params.areaId = "area";
  client = new QueryClient({ defaultOptions: { queries: { staleTime: 60_000, retry: false } } });
  vi.mocked(api.getThermalClusters).mockResolvedValue([cluster]);
});
afterEach(() => client.clear());

test("cold direct link shares one complete request between selector and form defaults", async () => {
  const response = deferred<ThermalCluster[]>();
  vi.mocked(api.getThermalClusters).mockReturnValue(response.promise);
  const { result } = renderHook(
    () => ({
      selector: useThermalClusters(scope),
      defaults: useThermalClusterDefaults({ ...scope, clusterId: "gas" }),
    }),
    { wrapper },
  );
  let defaults: Promise<unknown>;
  act(() => {
    defaults = result.current.defaults();
  });
  await act(async () => {
    response.resolve([cluster]);
    await defaults;
  });
  await waitFor(() => expect(result.current.selector.isSuccess).toBe(true));
  expect(await result.current.defaults()).toEqual({ ...cluster, group: "" });
  expect(api.getThermalClusters).toHaveBeenCalledTimes(1);
  expect(api.getThermalCluster).not.toHaveBeenCalled();
  expect(client.getQueryData(key)).toEqual([cluster]);
});

test("fresh list is reused on mount and background refresh preserves unsaved parameter edits", async () => {
  client.setQueryData(key, [cluster]);
  const view = render(<Parameters />, { wrapper });
  const input = await screen.findByRole("spinbutton", { name: capacityLabel });
  await waitFor(() => expect(input).toHaveValue(100));
  expect(api.getThermalClusters).not.toHaveBeenCalled();
  await userEvent.clear(input);
  await userEvent.type(input, "250");
  act(() => {
    client.setQueryData(key, [{ ...cluster, nominalCapacity: 999 }]);
  });
  view.rerender(<Parameters />);
  expect(input).toHaveValue(250);
  expect(screen.getByRole("button", { name: "global.save" })).toBeEnabled();
});

test("a new area with the same cluster ID receives its own form defaults", async () => {
  client.setQueryData(key, [cluster]);
  client.setQueryData(thermalKeys.list("study", "other"), [{ ...cluster, nominalCapacity: 42 }]);
  const view = render(<Parameters />, { wrapper });
  await waitFor(() =>
    expect(screen.getByRole("spinbutton", { name: capacityLabel })).toHaveValue(100),
  );
  params.areaId = "other";
  view.rerender(<Parameters />);
  await waitFor(() =>
    expect(screen.getByRole("spinbutton", { name: capacityLabel })).toHaveValue(42),
  );
});

test("successful parameter save sends dirty fields and retains the adapter's empty group", async () => {
  client.setQueryData(key, [cluster]);
  vi.mocked(api.updateThermalCluster).mockResolvedValue({ ...cluster, nominalCapacity: 250 });
  render(<Parameters />, { wrapper });
  const input = await screen.findByRole("spinbutton", { name: capacityLabel });
  await waitFor(() => expect(input).toHaveValue(100));
  await userEvent.clear(input);
  await userEvent.type(input, "250");
  await userEvent.click(screen.getByRole("button", { name: "global.save" }));
  await waitFor(() =>
    expect(api.updateThermalCluster).toHaveBeenCalledWith(
      {
        ...scope,
        clusterId: "gas",
        values: { nominalCapacity: 250 },
      },
      expect.anything(),
    ),
  );
  await waitFor(() => expect(screen.getByRole("button", { name: "global.save" })).toBeDisabled());
  expect(screen.getByRole("combobox", { name: "global.group" })).toHaveValue("");
  expect(input).toHaveValue(250);
});

test("failed parameter save retains edits and the existing form error feedback", async () => {
  client.setQueryData(key, [cluster]);
  const error = new Error("write failed");
  vi.mocked(api.updateThermalCluster).mockRejectedValue(error);
  render(<Parameters />, { wrapper });
  const input = await screen.findByRole("spinbutton", { name: capacityLabel });
  await waitFor(() => expect(input).toHaveValue(100));
  await userEvent.clear(input);
  await userEvent.type(input, "250");
  await userEvent.click(screen.getByRole("button", { name: "global.save" }));
  await waitFor(() => expect(notify).toHaveBeenCalledWith("form.submit.error", error));
  expect(input).toHaveValue(250);
  expect(client.getQueryData(key)).toEqual([cluster]);
  expect(screen.getByRole("button", { name: "global.save" })).toBeEnabled();
});

test("missing direct-link cluster returns a useful error from the complete list", async () => {
  const { result } = renderHook(
    () => useThermalClusterDefaults({ ...scope, clusterId: "missing" }),
    { wrapper },
  );
  await expect(result.current()).rejects.toThrow("study.modeling.thermals.notFound");
  expect(api.getThermalCluster).not.toHaveBeenCalled();
});

test("the real table loads an initially empty cache and keeps create optimism and rollback local", async () => {
  const response = deferred<ThermalCluster[]>();
  const creation = deferred<ThermalCluster>();
  vi.mocked(api.getThermalClusters).mockReturnValue(response.promise);
  vi.mocked(api.createThermalCluster).mockReturnValue(creation.promise);
  render(<Table />, { wrapper });
  await act(() => {
    response.resolve([cluster]);
  });
  expect(await screen.findByText("Gas")).toBeInTheDocument();
  await userEvent.click(screen.getByRole("button", { name: "button.add" }));
  await userEvent.click(screen.getByRole("button", { name: "Confirm create" }));
  expect(await screen.findByText("New")).toBeInTheDocument();
  expect(client.getQueryData(key)).toEqual([cluster]);
  await act(() => {
    creation.reject(new Error("creation failed"));
  });
  await waitFor(() => expect(screen.queryByText("New")).not.toBeInTheDocument());
  expect(screen.getByText("Gas")).toBeInTheDocument();
  expect(notify).toHaveBeenCalledWith("global.error.create", expect.any(Error));
});

test("the real table restores a failed deletion without changing the shared list", async () => {
  client.setQueryData(key, [cluster]);
  const deletion = deferred<void>();
  vi.mocked(api.deleteThermalClusters).mockReturnValue(deletion.promise);
  render(<Table />, { wrapper });
  await userEvent.click(await screen.findByText("Gas"));
  await userEvent.click(screen.getByRole("button", { name: "global.delete" }));
  await userEvent.click(screen.getByRole("button", { name: "Confirm delete" }));
  await waitFor(() => expect(screen.queryByText("Gas")).not.toBeInTheDocument());
  expect(client.getQueryData(key)).toEqual([cluster]);
  await act(() => {
    deletion.reject(new Error("deletion failed"));
  });
  expect(await screen.findByText("Gas")).toBeInTheDocument();
  expect(notify).toHaveBeenCalledWith("global.error.delete", expect.any(Error));
});

test("successful creation from an empty list replaces the pending row exactly once and updates totals", async () => {
  client.setQueryData(key, []);
  const creation = deferred<ThermalCluster>();
  const newCluster = { ...cluster, id: "new", name: "New" };
  vi.mocked(api.createThermalCluster).mockReturnValue(creation.promise);
  vi.mocked(api.getThermalClusters).mockResolvedValue([newCluster]);
  const view = render(<Table />, { wrapper });
  await userEvent.click(await screen.findByRole("button", { name: "button.add" }));
  await userEvent.click(screen.getByRole("button", { name: "Confirm create" }));
  expect(await screen.findByText("New")).toBeInTheDocument();
  expect(client.getQueryData(key)).toEqual([]);
  await act(() => {
    creation.resolve(newCluster);
  });
  await waitFor(() => expect(client.getQueryData(key)).toEqual([newCluster]));
  await waitFor(() => expect(view.container.querySelector("tfoot")).toHaveTextContent("200 / 200"));
  expect(screen.getAllByText("New")).toHaveLength(1);
});
