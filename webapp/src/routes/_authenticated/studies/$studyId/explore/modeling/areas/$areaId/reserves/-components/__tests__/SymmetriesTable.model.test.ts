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

import type { ReservesSymmetries } from "@/services/api/studies/areas/reserves/types";
import {
  addSymmetries,
  deleteSymmetryRows,
  duplicateSymmetryRow,
  fromApi,
  toApi,
  toggleReserve,
  validateGroups,
} from "../SymmetriesTable.model";

const CLUSTERS = [
  { id: "cluster_1", name: "Cluster 1" },
  { id: "cluster_2", name: "Cluster 2" },
];

describe("SymmetriesTable.model", () => {
  describe("fromApi / toApi", () => {
    test("round-trips the API payload", () => {
      const data: ReservesSymmetries = {
        cluster_1: [
          ["reserve_a", "reserve_b"],
          ["reserve_a", "reserve_c"],
        ],
      };

      const groups = fromApi(CLUSTERS, data);

      expect(groups).toHaveLength(2);
      expect(groups[0].symmetries.map((s) => s.index)).toEqual([1, 2]);
      expect(groups[0].symmetries.map((s) => [...s.reserves])).toEqual([
        ["reserve_a", "reserve_b"],
        ["reserve_a", "reserve_c"],
      ]);

      expect(toApi(groups)).toEqual(data);
    });

    test("gives every cluster a row group, even with no symmetries (RM-01)", () => {
      const groups = fromApi(CLUSTERS, {});

      expect(groups.map((g) => g.clusterId)).toEqual(["cluster_1", "cluster_2"]);
      expect(groups.every((g) => g.symmetries.length === 0)).toBe(true);
      expect(toApi(groups)).toEqual({});
    });
  });

  describe("addSymmetries", () => {
    test("appends unchecked symmetries with sequential indices (CA-02)", () => {
      const groups = fromApi(CLUSTERS, {});
      const next = addSymmetries(groups, "cluster_1", 3);

      const rows = next.find((g) => g.clusterId === "cluster_1")!.symmetries;
      expect(rows.map((r) => r.index)).toEqual([1, 2, 3]);
      expect(rows.every((r) => r.reserves.size === 0)).toBe(true);
    });

    test("does not affect other clusters", () => {
      const groups = fromApi(CLUSTERS, {});
      const next = addSymmetries(groups, "cluster_1", 1);

      expect(next.find((g) => g.clusterId === "cluster_2")!.symmetries).toHaveLength(0);
    });
  });

  describe("deleteSymmetryRows", () => {
    test("renumbers subsequent symmetries after deleting a middle row (RM-02)", () => {
      const groups = fromApi(CLUSTERS, {
        cluster_1: [["a", "b"], ["a", "c"], ["a", "d"]],
      });
      const middleUiId = groups[0].symmetries[1].uiId;

      const next = deleteSymmetryRows(groups, new Set([middleUiId]));

      const rows = next[0].symmetries;
      expect(rows.map((r) => r.index)).toEqual([1, 2]);
      expect(rows.map((r) => [...r.reserves])).toEqual([["a", "b"], ["a", "d"]]);
    });

    test("keeps the cluster group row when it reaches zero symmetries (RM-06)", () => {
      const groups = fromApi(CLUSTERS, { cluster_1: [["a", "b"]] });
      const uiId = groups[0].symmetries[0].uiId;

      const next = deleteSymmetryRows(groups, new Set([uiId]));

      expect(next.map((g) => g.clusterId)).toEqual(["cluster_1", "cluster_2"]);
      expect(next[0].symmetries).toHaveLength(0);
      expect(toApi(next)).toEqual({});
    });

    test("deletes across multiple clusters in one call", () => {
      const groups = fromApi(CLUSTERS, {
        cluster_1: [["a", "b"]],
        cluster_2: [["a", "b"]],
      });
      const uiIds = new Set(groups.flatMap((g) => g.symmetries.map((s) => s.uiId)));

      const next = deleteSymmetryRows(groups, uiIds);

      expect(next.every((g) => g.symmetries.length === 0)).toBe(true);
    });
  });

  describe("duplicateSymmetryRow", () => {
    test("inserts an exact copy immediately after and renumbers (RM-05)", () => {
      const groups = fromApi(CLUSTERS, {
        cluster_1: [["a", "b"], ["c", "d"]],
      });
      const firstUiId = groups[0].symmetries[0].uiId;

      const next = duplicateSymmetryRow(groups, firstUiId);

      const rows = next[0].symmetries;
      expect(rows).toHaveLength(3);
      expect(rows.map((r) => r.index)).toEqual([1, 2, 3]);
      expect([...rows[1].reserves]).toEqual(["a", "b"]);
      expect(rows[1].uiId).not.toBe(firstUiId);
      expect([...rows[2].reserves]).toEqual(["c", "d"]);
    });
  });

  describe("toggleReserve", () => {
    test("checks and unchecks independently of other symmetries (RM-03)", () => {
      let groups = fromApi(CLUSTERS, { cluster_1: [[], []] });
      const [row1, row2] = groups[0].symmetries;

      groups = toggleReserve(groups, row1.uiId, "reserve_a");
      groups = toggleReserve(groups, row2.uiId, "reserve_a");

      expect([...groups[0].symmetries[0].reserves]).toEqual(["reserve_a"]);
      expect([...groups[0].symmetries[1].reserves]).toEqual(["reserve_a"]);

      groups = toggleReserve(groups, row1.uiId, "reserve_a");
      expect(groups[0].symmetries[0].reserves.size).toBe(0);
    });
  });

  describe("validateGroups", () => {
    test("flags symmetries with fewer than 2 checked reserves", () => {
      const groups = fromApi(CLUSTERS, {
        cluster_1: [[], ["a"], ["a", "b"]],
      });

      const errors = validateGroups(groups);

      expect(errors).toHaveLength(2);
      expect(errors.map((e) => e.index)).toEqual([1, 2]);
    });

    test("returns no errors for a fully valid matrix", () => {
      const groups = fromApi(CLUSTERS, { cluster_1: [["a", "b"]] });
      expect(validateGroups(groups)).toEqual([]);
    });
  });
});
