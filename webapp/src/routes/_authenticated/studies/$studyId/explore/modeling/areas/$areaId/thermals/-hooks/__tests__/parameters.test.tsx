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

import "./setup";

import { thermalKeys } from "@/queries/thermals/keys";
import * as api from "@/services/api/studies/areas/thermals";
import type { QueryClient } from "@tanstack/react-query";
import { createQueryClient, createQueryWrapper } from "@/tests/queryUtils";
import { cluster } from "./fixtures";
import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route } from "../../$thermalId/parameters";

const { params, notify } = vi.hoisted(() => ({
  params: { studyId: "study", areaId: "area", thermalId: "gas" },
  notify: vi.fn(),
}));
vi.mock("@/hooks/useFormBlocker", () => ({ default: vi.fn() }));
vi.mock("@/hooks/useEnqueueErrorSnackbar", () => ({ default: () => notify }));
vi.mock("@/routes/_authenticated/studies/$studyId/-hooks/useStudy", () => ({
  default: () => ({ id: params.studyId, version: "9.3.0" }),
}));
vi.mock("@tanstack/react-router", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@tanstack/react-router")>()),
  createFileRoute: () => (options: object) => ({ options, useParams: () => params }),
}));

let wrapper: ReturnType<typeof createQueryWrapper>;

function Parameters() {
  const Component = Route.options.component;

  if (!Component) {
    throw new Error("Missing parameters component");
  }

  return <Component />;
}

const capacityLabel = "study.modeling.clusters.nominalCapacity";
const scope = { studyId: "study", areaId: "area" };
const key = thermalKeys.list(scope.studyId, scope.areaId);
let client: QueryClient;

beforeAll(async () => {
  // The router code-splits this component.
  await Route.options.component?.preload?.();
});

beforeEach(() => {
  vi.clearAllMocks();
  params.areaId = "area";
  params.thermalId = "gas";

  client = createQueryClient();
  wrapper = createQueryWrapper(client);

  vi.mocked(api.getThermalClusters).mockReset().mockResolvedValue([cluster]);
});

afterEach(() => client.clear());

describe("Thermal parameters", () => {
  test("preserves edits across refetches and saves only changed fields", async () => {
    client.setQueryData(key, [cluster]);
    vi.mocked(api.updateThermalCluster)
      .mockReset()
      .mockResolvedValue({ ...cluster, nominalCapacity: 250, unitCount: 5 });

    render(<Parameters />, { wrapper });
    const input = await screen.findByRole("spinbutton", { name: capacityLabel });
    await userEvent.clear(input);
    await userEvent.type(input, "250");

    // Another writer changed the capacity and unit count while this form was being edited.
    vi.mocked(api.getThermalClusters).mockResolvedValue([
      { ...cluster, nominalCapacity: 999, unitCount: 5 },
    ]);

    await act(async () => {
      await client.invalidateQueries({ queryKey: key });
    });

    expect(input).toHaveValue(250);

    await userEvent.click(screen.getByRole("button", { name: "global.save" }));

    await waitFor(() =>
      expect(api.updateThermalCluster).toHaveBeenCalledWith(
        { ...scope, clusterId: "gas", values: { nominalCapacity: 250 } },
        expect.anything(),
      ),
    );
    await waitFor(() => expect(screen.getByRole("button", { name: "global.save" })).toBeDisabled());
    expect(input).toHaveValue(250);
    expect(client.getQueryData(key)).toEqual([{ ...cluster, nominalCapacity: 250, unitCount: 5 }]);
    expect(api.getThermalClusters).toHaveBeenCalledTimes(1);
  });

  test("resets defaults when the area changes", async () => {
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
});
