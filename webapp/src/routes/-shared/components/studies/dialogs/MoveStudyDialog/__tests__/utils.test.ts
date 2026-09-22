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

import type { StudyMetadata } from "@/types/types";
import { computeAllowSubmitOnPristine, getInitialDirectoryId } from "../utils";

function makeStudy(overrides: Partial<StudyMetadata> = {}): StudyMetadata {
  return {
    id: "study-1",
    name: "Study 1",
    managed: true,
    ...overrides,
  } as StudyMetadata;
}

describe("getInitialDirectoryId", () => {
  test("returns null for empty array", () => {
    expect(getInitialDirectoryId([])).toBeNull();
  });

  test("single study: returns null when the study is at root", () => {
    const study = makeStudy({ directoryId: null });
    expect(getInitialDirectoryId([study])).toBeNull();
  });

  test("single study: returns null when directoryId is undefined (treated as root)", () => {
    const study = makeStudy({ directoryId: undefined });
    expect(getInitialDirectoryId([study])).toBeNull();
  });

  test("multiple studies: returns the shared directoryId when all are in the same directory", () => {
    const studies = [
      makeStudy({ id: "s1", directoryId: "dir-a" }),
      makeStudy({ id: "s2", directoryId: "dir-a" }),
      makeStudy({ id: "s3", directoryId: "dir-a" }),
    ];
    expect(getInitialDirectoryId(studies)).toBe("dir-a");
  });

  test("multiple studies: returns null when all are at root", () => {
    const studies = [
      makeStudy({ id: "s1", directoryId: null }),
      makeStudy({ id: "s2", directoryId: null }),
    ];
    expect(getInitialDirectoryId(studies)).toBeNull();
  });

  test("multiple studies: returns null when in different directories", () => {
    const studies = [
      makeStudy({ id: "s1", directoryId: "dir-a" }),
      makeStudy({ id: "s2", directoryId: "dir-b" }),
    ];
    expect(getInitialDirectoryId(studies)).toBeNull();
  });

  test("multiple studies: returns null when one is at root and another is not", () => {
    const studies = [
      makeStudy({ id: "s1", directoryId: null }),
      makeStudy({ id: "s2", directoryId: "dir-a" }),
    ];
    expect(getInitialDirectoryId(studies)).toBeNull();
  });
});

describe("computeAllowSubmitOnPristine", () => {
  test("single study at root → false (prevents no-op root → root)", () => {
    const study = makeStudy({ directoryId: null });
    expect(computeAllowSubmitOnPristine(null, [study])).toBe(false);
  });

  test("multiple studies all at root → false (prevents no-op bulk root → root)", () => {
    const studies = [
      makeStudy({ id: "s1", directoryId: null }),
      makeStudy({ id: "s2", directoryId: null }),
    ];
    expect(computeAllowSubmitOnPristine(null, studies)).toBe(false);
  });

  test("multiple studies in same non-root directory → false (initialDirectoryId is non-null)", () => {
    const studies = [
      makeStudy({ id: "s1", directoryId: "dir-a" }),
      makeStudy({ id: "s2", directoryId: "dir-a" }),
    ];
    expect(computeAllowSubmitOnPristine("dir-a", studies)).toBe(false);
  });

  test("multiple studies, some at root and some not → true", () => {
    const studies = [
      makeStudy({ id: "s1", directoryId: null }),
      makeStudy({ id: "s2", directoryId: "dir-a" }),
    ];
    expect(computeAllowSubmitOnPristine(null, studies)).toBe(true);
  });

  test("empty studies array → false", () => {
    expect(computeAllowSubmitOnPristine(null, [])).toBe(false);
  });
});
