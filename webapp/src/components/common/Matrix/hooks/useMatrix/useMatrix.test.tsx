/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
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

import { renderHook, act, waitFor } from "@testing-library/react";
import { useMatrix } from "../useMatrix";
import * as apiMatrix from "@/services/api/matrix";
import * as apiStudy from "@/services/api/study";
import * as rawStudy from "@/services/api/studies/raw";
import {
  Operator,
  StudyOutputDownloadLevelDTO,
  type MatrixEditDTO,
  type MatrixIndex,
} from "@/types/types";
import type { GridUpdate, MatrixDataDTO } from "../../shared/types";
import { GridCellKind } from "@glideapps/glide-data-grid";

vi.mock("@/services/api/matrix");
vi.mock("@/services/api/study");
vi.mock("@/services/api/studies/raw");
vi.mock("@/hooks/usePrompt");

// TODO: refactor fixtures, utils functions, and types in dedicated files
const DATA = {
  studyId: "study123",
  url: "https://studies/study123/matrix",
  matrixData: {
    data: [
      [1, 2],
      [3, 4],
    ],
    columns: [0, 1],
    index: [0, 1],
  } as MatrixDataDTO,
  matrixIndex: {
    start_date: "2023-01-01",
    steps: 2,
    first_week_size: 7,
    level: StudyOutputDownloadLevelDTO.DAILY,
  } as MatrixIndex,
};

const createGridUpdate = (row: number, col: number, value: number): GridUpdate => ({
  coordinates: [row, col],
  value: {
    kind: GridCellKind.Number,
    data: value,
    displayData: value.toString(),
    allowOverlay: true,
  },
});

interface SetupOptions {
  mockData?: MatrixDataDTO;
  mockIndex?: MatrixIndex;
}

const setupHook = async ({
  mockData = DATA.matrixData,
  mockIndex = DATA.matrixIndex,
}: SetupOptions = {}) => {
  vi.mocked(apiStudy.getStudyData).mockResolvedValue(mockData);
  vi.mocked(apiMatrix.getStudyMatrixIndex).mockResolvedValue(mockIndex);

  const hook = renderHook(() => useMatrix(DATA.studyId, DATA.url, true, true, true));

  await waitFor(() => {
    expect(hook.result.current.isLoading).toBe(false);
  });

  return hook;
};

const performEdit = async (
  hook: Awaited<ReturnType<typeof setupHook>>,
  updates: GridUpdate | GridUpdate[],
) => {
  act(() => {
    if (Array.isArray(updates)) {
      hook.result.current.handleMultipleCellsEdit(updates);
    } else {
      hook.result.current.handleCellEdit(updates);
    }
  });
};

describe("useMatrix", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("Initialization", () => {
    test("should fetch and initialize matrix data", async () => {
      const hook = await setupHook();

      expect(hook.result.current.data).toEqual(DATA.matrixData.data);
      expect(hook.result.current.columns.length).toBeGreaterThan(0);
      expect(hook.result.current.dateTime.length).toBeGreaterThan(0);
      expect(hook.result.current.isLoading).toBe(false);
    });
  });

  describe("Edit operations", () => {
    test("should handle single cell edit", async () => {
      const hook = await setupHook();
      const update = createGridUpdate(0, 1, 5);

      await performEdit(hook, update);

      expect(hook.result.current.data[1][0]).toBe(5);
      expect(hook.result.current.pendingUpdatesCount).toBe(1);
    });

    test("should handle multiple cell edits", async () => {
      const hook = await setupHook();
      const updates = [createGridUpdate(0, 1, 5), createGridUpdate(1, 0, 6)];

      await performEdit(hook, updates);

      expect(hook.result.current.data[1][0]).toBe(5);
      expect(hook.result.current.data[0][1]).toBe(6);
      expect(hook.result.current.pendingUpdatesCount).toBe(1);
    });

    test("should save updates correctly", async () => {
      vi.mocked(apiMatrix.updateMatrix).mockResolvedValue(undefined);
      const hook = await setupHook();

      await performEdit(hook, createGridUpdate(0, 1, 5));

      await act(async () => {
        await hook.result.current.handleSaveUpdates();
      });

      const expectedEdit: MatrixEditDTO = {
        coordinates: [[1, 0]],
        operation: { operation: Operator.EQ, value: 5 },
      };

      expect(apiMatrix.updateMatrix).toHaveBeenCalledWith(DATA.studyId, DATA.url, [expectedEdit]);
      expect(hook.result.current.pendingUpdatesCount).toBe(0);
    });
  });

  describe("File operations", () => {
    test("should handle file import", async () => {
      const mockFile = new File([""], "test.csv", { type: "text/csv" });
      vi.mocked(rawStudy.uploadFile).mockResolvedValue();

      const hook = await setupHook();

      await act(async () => {
        await hook.result.current.handleUpload(mockFile);
      });

      expect(rawStudy.uploadFile).toHaveBeenCalledWith({
        file: mockFile,
        studyId: DATA.studyId,
        path: DATA.url,
      });
    });
  });

  describe("Undo/Redo functionality", () => {
    test("should initialize with correct undo/redo states", async () => {
      const hook = await setupHook();

      expect(hook.result.current.canUndo).toBe(false);
      expect(hook.result.current.canRedo).toBe(false);
    });

    test("should update states after edit operations", async () => {
      const hook = await setupHook();
      const update = createGridUpdate(0, 1, 5);

      // Initial edit
      await performEdit(hook, update);
      expect(hook.result.current.canUndo).toBe(true);
      expect(hook.result.current.canRedo).toBe(false);

      // Undo
      act(() => hook.result.current.undo());
      expect(hook.result.current.canUndo).toBe(false);
      expect(hook.result.current.canRedo).toBe(true);

      // Redo
      act(() => hook.result.current.redo());
      expect(hook.result.current.canUndo).toBe(true);
      expect(hook.result.current.canRedo).toBe(false);
    });

    test("should clear redo history after new edit", async () => {
      const hook = await setupHook();

      // Create edit history
      await performEdit(hook, createGridUpdate(0, 1, 5));
      act(() => hook.result.current.undo());
      expect(hook.result.current.canRedo).toBe(true);

      // New edit should clear redo history
      await performEdit(hook, createGridUpdate(1, 0, 6));
      expect(hook.result.current.canUndo).toBe(true);
      expect(hook.result.current.canRedo).toBe(false);
    });

    test("should restore initial state after full undo", async () => {
      const hook = await setupHook();
      const initialData = [...DATA.matrixData.data];

      await performEdit(hook, createGridUpdate(0, 1, 5));
      act(() => hook.result.current.undo());

      expect(hook.result.current.data).toEqual(initialData);
      expect(hook.result.current.canUndo).toBe(false);
      expect(hook.result.current.canRedo).toBe(true);
    });
  });
});
