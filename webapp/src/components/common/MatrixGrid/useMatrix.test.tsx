import { renderHook, act, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach } from "vitest";
import { useMatrix } from "./useMatrix";
import * as apiMatrix from "../../../services/api/matrix";
import * as apiStudy from "../../../services/api/study";
import {
  MatrixEditDTO,
  MatrixIndex,
  Operator,
  StudyOutputDownloadLevelDTO,
} from "../../../common/types";
import { MatrixData } from "./types";

vi.mock("../../../services/api/matrix");
vi.mock("../../../services/api/study");

describe("useMatrix", () => {
  const mockStudyId = "study123";
  const mockUrl = "http://studies/study123/matrix";

  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockMatrixData: MatrixData = {
    data: [
      [1, 2],
      [3, 4],
    ],
    columns: [0, 1],
    index: [0, 1],
  };

  const mockMatrixIndex: MatrixIndex = {
    start_date: "2023-01-01",
    steps: 2,
    first_week_size: 7,
    level: StudyOutputDownloadLevelDTO.DAILY, // TODO remove this, fix the type
  };

  it("should fetch matrix data and index on mount", async () => {
    vi.mocked(apiStudy.getStudyData).mockResolvedValue(mockMatrixData);
    vi.mocked(apiMatrix.getStudyMatrixIndex).mockResolvedValue(mockMatrixIndex);

    const { result } = renderHook(() =>
      useMatrix(mockStudyId, mockUrl, true, true),
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.matrixData).toEqual(mockMatrixData);
    expect(result.current.columns.length).toBeGreaterThan(0);
    expect(result.current.dateTime.length).toBeGreaterThan(0);
  });

  it("should handle cell edit", async () => {
    const mockMatrixData: MatrixData = {
      data: [
        [1, 2],
        [3, 4],
      ],
      columns: [0, 1],
      index: [0, 1],
    };

    const mockMatrixIndex: MatrixIndex = {
      start_date: "2023-01-01",
      steps: 2,
      first_week_size: 7,
      level: StudyOutputDownloadLevelDTO.DAILY,
    };

    vi.mocked(apiStudy.getStudyData).mockResolvedValue(mockMatrixData);
    vi.mocked(apiMatrix.getStudyMatrixIndex).mockResolvedValue(mockMatrixIndex);
    vi.mocked(apiMatrix.editMatrix).mockResolvedValue(undefined);

    const { result } = renderHook(() =>
      useMatrix(mockStudyId, mockUrl, true, true),
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.handleCellEdit([0, 1], 5);
    });

    const expectedEdit: MatrixEditDTO = {
      coordinates: [[1, 0]],
      operation: {
        operation: Operator.EQ,
        value: 5,
      },
    };

    expect(apiMatrix.editMatrix).toHaveBeenCalledWith(mockStudyId, mockUrl, [
      expectedEdit,
    ]);
  });

  it("should handle file import", async () => {
    const mockFile = new File([""], "test.csv", { type: "text/csv" });
    const mockImportFile = vi.fn().mockResolvedValue({});
    vi.mocked(apiStudy.importFile).mockImplementation(mockImportFile);

    const { result } = renderHook(() =>
      useMatrix(mockStudyId, mockUrl, true, true),
    );

    await act(async () => {
      await result.current.handleImport(mockFile);
    });

    expect(apiStudy.importFile).toHaveBeenCalledWith(
      mockFile,
      mockStudyId,
      mockUrl,
    );
  });
});
